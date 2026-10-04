# Standard Library
from collections import defaultdict
from decimal import Decimal
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI, Query, Schema

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.api.character import create_ledger_details
from ledger.api.helpers.core import (
    get_available_years,
    get_corporationowner_or_none,
)
from ledger.api.schema import (
    AltLedgerSchema,
    AltSchema,
    BillboardSchema,
    CorporationLedgerFilter,
    DivisionSchema,
    EntitySchema,
    ErrorSchema,
    LedgerDetailsResponse,
    LedgerResponse,
    LedgerSchema,
    OwnerSchema,
    Section,
)
from ledger.constants import NPC_ENTITIES
from ledger.helpers.billboard import BillboardSystem
from ledger.helpers.eveonline import get_character_portrait_url
from ledger.helpers.ref_type import RefTypeManager
from ledger.models.corporationaudit import (
    CorporationOwner,
    CorporationWalletJournalEntry,
)
from ledger.models.general import EveEntity
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class LedgerEntitySchema(Schema):
    entity: EntitySchema
    ledger: LedgerSchema
    # Contribution of each character of an auth member.
    members: list[AltLedgerSchema] = []


class CorporationLedgerResponse(LedgerResponse):
    """
    Schema for Corporation Ledger Response.

    Attributes:
        entities (list[LedgerEntitySchema]): The list of ledger entities.
        divisions (list[DivisionSchema]): The wallet divisions to choose from.
    """

    entities: list[LedgerEntitySchema]
    divisions: list[DivisionSchema] = []


class CorporationApiEndpoints:
    tags = ["Corporation"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/ledger/",
            response={
                HTTPStatus.OK: CorporationLedgerResponse,
                HTTPStatus.FORBIDDEN: ErrorSchema,
                HTTPStatus.NOT_FOUND: ErrorSchema,
            },
            tags=self.tags,
            summary="Get the ledger of a corporation, optionally for one division",
        )
        def get_corporation_ledger(
            request: WSGIRequest,
            corporation_id: int,
            filters: Query[CorporationLedgerFilter],
        ):
            return self._ledger_api_response(
                request=request, corporation_id=corporation_id, filters=filters
            )

    def _sum_by_ref_types(
        self, entry_list: list[dict], ref_types: list[str], sign: str | None = None
    ) -> Decimal:
        """Sum amounts in entry_list filtered by ref_types and sign.

        Args:
            entry_list (list[dict]): List of ledger entry dicts.
            ref_types (list[str]): Reference types to include.
            sign (str|None): If "positive", include only positive amounts; if "negative", only negative amounts.
        Returns:
            Decimal: The summed amount.
        """
        total = Decimal("0.00")
        for r in entry_list:
            if r.get("ref_type") in ref_types:
                amt = r.get("amount") or Decimal("0.00")
                if sign == "positive" and amt <= 0:
                    continue
                if sign == "negative" and amt >= 0:
                    continue
                total += amt
        return total

    def _ledger_from_entries(self, entry_list: list[dict]) -> LedgerSchema:
        """Build the ledger summary of the given journal entries."""
        bounty = self._sum_by_ref_types(entry_list, RefTypeManager.BOUNTY_PRIZES)
        ess = self._sum_by_ref_types(entry_list, RefTypeManager.ESS_TRANSFER)
        costs = self._sum_by_ref_types(
            entry_list, RefTypeManager.ledger_ref_types(), sign="negative"
        )
        miscellaneous = self._sum_by_ref_types(
            entry_list, RefTypeManager.ledger_ref_types(), sign="positive"
        )
        return LedgerSchema(
            bounty=bounty,
            ess=ess,
            costs=costs,
            miscellaneous=miscellaneous,
            total=sum([bounty, ess, miscellaneous, costs]),
        )

    def _member_ledgers(
        self,
        entity: EntitySchema,
        entries_by_entity: dict[int, list[dict]],
        counted_entry_ids: set[int],
    ) -> list[AltLedgerSchema]:
        """Split the counted entries of an entity by character.

        An entry between two characters of the entity is credited to the first one only,
        so that the contributions add up to the entity ledger.
        """
        claimed: set[int] = set()
        members = []
        for alt in entity.alts:
            alt_entries = [
                r
                for r in entries_by_entity.get(alt.character_id, [])
                if r["entry_id"] in counted_entry_ids and r["entry_id"] not in claimed
            ]
            claimed.update(r["entry_id"] for r in alt_entries)
            members.append(
                AltLedgerSchema(
                    character_id=alt.character_id,
                    character_name=alt.character_name,
                    icon=alt.icon,
                    ledger=self._ledger_from_entries(alt_entries),
                )
            )
        return members

    def _process_entity_entries(
        self,
        entity: EntitySchema,
        entries_by_entity: dict[int, list[dict]],
        processed_entry_ids: set[int],
    ) -> LedgerEntitySchema | None:
        """
        Aggregate the journal entries of an entity (and its alts).

        Entries that were already assigned to an entity are skipped.

        Args:
            entity (EntitySchema): The entity for which to process entries.
            entries_by_entity (dict[int, list[dict]]): The mapping of entity IDs to their ledger entries.
            processed_entry_ids (set[int]): Already processed entry IDs, updated in place.
        Returns:
            LedgerEntitySchema | None: The entity ledger or None if it has no entries.
        """
        combined_entries: list[dict] = list(entries_by_entity.get(entity.entity_id, []))
        for alt_id in entity.alt_ids:
            combined_entries.extend(entries_by_entity.get(alt_id, []))

        # Deduplicate by entry_id (an entry may appear under multiple alt_ids)
        unique: dict[int, dict] = {
            r["entry_id"]: r
            for r in combined_entries
            if r.get("entry_id") not in processed_entry_ids
        }

        # Skip Entity if no Ledger Entries
        if not unique:
            return None

        entry_list = list(unique.values())
        ledger = self._ledger_from_entries(entry_list)
        members = (
            self._member_ledgers(
                entity=entity,
                entries_by_entity=entries_by_entity,
                counted_entry_ids=set(unique),
            )
            if entity.alts
            else []
        )

        # Mark these entries as processed so they won't be used again
        processed_entry_ids.update(unique.keys())
        return LedgerEntitySchema(entity=entity, ledger=ledger, members=members)

    def process_member_ledger_data(
        self,
        entity_ids: set[int],
        entries_by_entity: dict[int, list[dict]],
        processed_entry_ids: set[int],
        entity_ledger_list: list[LedgerEntitySchema],
    ) -> list[int]:
        """
        Process the ledger data for auth member entities (main character + alts).

        Returns:
            list[int]: The character IDs that belong to an auth member.
        """
        accounts = UserProfile.objects.filter(
            main_character__isnull=False,
        ).order_by(
            "user__profile__main_character__character_name",
        )

        auth_entity_ids = []
        for account in accounts:
            alts = account.user.character_ownerships.all()
            existing_alts = alts.filter(
                character__character_id__in=entity_ids.intersection(
                    alts.values_list("character__character_id", flat=True)
                )
            ).select_related("character")
            alt_characters = [alt.character for alt in existing_alts]

            # Skip if no characters in Corporation
            if not alt_characters:
                continue

            alt_ids = [char.character_id for char in alt_characters]
            response_ledger = self._process_entity_entries(
                entity=EntitySchema(
                    entity_id=account.main_character.character_id,
                    entity_name=account.main_character.character_name,
                    alt_ids=alt_ids,
                    alts=[
                        AltSchema(
                            character_id=char.character_id,
                            character_name=char.character_name,
                            icon=get_character_portrait_url(
                                character_id=char.character_id,
                                character_name=char.character_name,
                                size=32,
                            ),
                        )
                        for char in alt_characters
                    ],
                    icon=get_character_portrait_url(
                        character_id=account.main_character.character_id,
                        character_name=account.main_character.character_name,
                        size=32,
                    ),
                ),
                entries_by_entity=entries_by_entity,
                processed_entry_ids=processed_entry_ids,
            )
            auth_entity_ids.extend(alt_ids)
            if response_ledger is not None:
                entity_ledger_list.append(response_ledger)
        return auth_entity_ids

    def _process_ledger_data(
        self,
        entities: list[EveEntity],
        entries_by_entity: dict[int, list[dict]],
        processed_entry_ids: set[int],
        entity_ledger_list: list[LedgerEntitySchema],
    ) -> list[LedgerEntitySchema]:
        """Process the ledger data for the given entities."""
        for entity in entities:
            response_ledger = self._process_entity_entries(
                entity=EntitySchema(
                    entity_id=entity.eve_id,
                    entity_name=entity.name,
                    icon=entity.get_portrait(size=32),
                ),
                entries_by_entity=entries_by_entity,
                processed_entry_ids=processed_entry_ids,
            )
            if response_ledger is not None:
                entity_ledger_list.append(response_ledger)

        return entity_ledger_list

    def generate_entity_data(
        self, owner: CorporationOwner, filters: CorporationLedgerFilter
    ) -> tuple[list[LedgerEntitySchema], BillboardSchema]:
        """
        Generate the ledger and billboard data for a corporation owner.

        Args:
            owner (CorporationOwner): The corporation owner object.
            filters (CorporationLedgerFilter): The requested date range and division.
        Returns:
            tuple[list[LedgerEntitySchema], BillboardSchema]: Ledger rows and chart data.
        """
        corp_journal = filters.filter(
            CorporationWalletJournalEntry.objects.filter(division__corporation=owner)
            # Exclude Zero Amount Entries
            .exclude(amount=Decimal("0.00"))
            # Exclude Internal Transfers
            .exclude(
                first_party_id=owner.eve_corporation.corporation_id,
                second_party_id=owner.eve_corporation.corporation_id,
            )
        ).order_by("-date")

        # Skip Corporation if no Ledger Entries
        if not corp_journal.exists():
            return [], BillboardSchema()

        entity_ids = set()
        entity_ledger_list: list[LedgerEntitySchema] = []
        processed_entry_ids: set[int] = set()
        entries_by_entity: dict[int, list[dict]] = defaultdict(list)

        for row in corp_journal.values(
            "entry_id",
            "amount",
            "ref_type",
            "first_party_id",
            "second_party_id",
            "date",
        ):
            a = row.get("first_party_id")
            b = row.get("second_party_id")
            if a:
                entries_by_entity[a].append(row)
                entity_ids.add(a)

            # Only append second party if different from first to avoid double-counting
            if b and b != a:
                entries_by_entity[b].append(row)
                entity_ids.add(b)

        # Process Auth Entities (Members) First
        auth_entity_ids = self.process_member_ledger_data(
            entity_ids=entity_ids,
            entries_by_entity=entries_by_entity,
            processed_entry_ids=processed_entry_ids,
            entity_ledger_list=entity_ledger_list,
        )

        # Remaining Entities without Auth Entities, NPCs and the Corporation itself
        entities = (
            EveEntity.objects.filter(eve_id__in=entity_ids)
            .exclude(eve_id__in=auth_entity_ids)
            .exclude(eve_id__in=NPC_ENTITIES)
            .exclude(eve_id=owner.eve_corporation.corporation_id)
            .order_by("name")
        )
        # NPC Entities Last
        npc_entities = EveEntity.objects.filter(eve_id__in=NPC_ENTITIES).order_by(
            "name"
        )

        for entity_group in (list(entities), list(npc_entities)):
            self._process_ledger_data(
                entities=entity_group,
                entries_by_entity=entries_by_entity,
                processed_entry_ids=processed_entry_ids,
                entity_ledger_list=entity_ledger_list,
            )

        xy_chart, chord_chart = BillboardSystem().create_billboards(
            filters=filters,
            wallet_journal=corp_journal,
            ledger_list=entity_ledger_list,
        )
        return entity_ledger_list, BillboardSchema(
            xy_chart=xy_chart, chord_chart=chord_chart
        )

    def _ledger_api_response(
        self, request, corporation_id: int, filters: CorporationLedgerFilter
    ) -> CorporationLedgerResponse | tuple[int, dict]:
        """Build the ledger response for a corporation and the given date."""
        perms, owner = get_corporationowner_or_none(
            request=request, corporation_id=corporation_id
        )

        if owner is None:
            return HTTPStatus.NOT_FOUND, {
                "error": _("Corporation not found in Ledger.")
            }

        if perms is False:
            return HTTPStatus.FORBIDDEN, {
                "error": _("You do not have permission to view this corporation.")
            }

        entity_ledger_list, billboard = self.generate_entity_data(
            owner=owner, filters=filters
        )

        return CorporationLedgerResponse(
            owner=OwnerSchema(
                character_id=owner.eve_corporation.corporation_id,
                character_name=owner.eve_corporation.corporation_name,
                icon=owner.get_portrait(),
            ),
            entities=entity_ledger_list,
            billboard=billboard,
            years=get_available_years(
                CorporationWalletJournalEntry.objects.filter(
                    division__corporation=owner
                )
            ),
            divisions=[
                DivisionSchema(
                    division_id=division.division_id, name=division.name or ""
                )
                for division in owner.ledger_corporation_division.order_by(
                    "division_id"
                )
            ],
        )


class CorporationDetailsApiEndpoints:
    tags = ["Corporation Details"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/details/",
            response={
                HTTPStatus.OK: LedgerDetailsResponse,
                HTTPStatus.FORBIDDEN: ErrorSchema,
                HTTPStatus.NOT_FOUND: ErrorSchema,
            },
            tags=self.tags,
            summary="Get the income and cost breakdown of a corporation entity",
        )
        def get_corporation_ledger_details(
            request: WSGIRequest,
            corporation_id: int,
            entity_id: int,
            filters: Query[CorporationLedgerFilter],
            section: Section = "summary",
        ):
            return self._ledger_details_api_response(
                request=request,
                corporation_id=corporation_id,
                entity_id=entity_id,
                filters=filters,
                section=section,
            )

    def _check_auth_account(
        self,
        owner: CorporationOwner,
        entity_id: int,
    ) -> list[int] | None:
        """Return the alt IDs if the entity_id belongs to an auth account."""
        for member in owner.auth_accounts:
            alt_ids = list(
                member.user.character_ownerships.all().values_list(
                    "character__character_id", flat=True
                )
            )
            if entity_id in alt_ids:
                return alt_ids
        return None

    def create_entity_details(
        self,
        owner: CorporationOwner,
        entity_id: int,
        filters: CorporationLedgerFilter,
        section: Section,
    ) -> LedgerDetailsResponse:
        """Create the category breakdown for an entity of the corporation."""
        # Check if Entity is a Member
        alt_ids = self._check_auth_account(owner=owner, entity_id=entity_id)

        entity_query = Q(first_party_id=entity_id) | Q(second_party_id=entity_id)
        if alt_ids is not None:
            entity_query = Q(first_party_id__in=alt_ids) | Q(
                second_party_id__in=alt_ids
            )
        elif entity_id == owner.eve_corporation.corporation_id:
            # Corporation itself includes all entries
            entity_query = Q()

        wallet_journal = filters.filter(
            CorporationWalletJournalEntry.objects.filter(
                entity_query, division__corporation=owner
            )
            # Exclude Zero Amount Entries
            .exclude(amount=Decimal("0.00"))
            # Exclude Internal Transfers
            .exclude(
                first_party_id=owner.eve_corporation.corporation_id,
                second_party_id=owner.eve_corporation.corporation_id,
            )
        )

        # Corporation contracts count for the corporation itself
        if alt_ids is not None:
            wallet_journal = wallet_journal.exclude(
                ref_type="contract_price_payment_corp",
                second_party_id__in=alt_ids,
            )

        return create_ledger_details(
            journal=wallet_journal, filters=filters, section=section
        )

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def _ledger_details_api_response(
        self,
        request: WSGIRequest,
        corporation_id: int,
        entity_id: int,
        filters: CorporationLedgerFilter,
        section: Section,
    ) -> LedgerDetailsResponse | tuple[int, dict]:
        """Build the details response for a corporation entity and the given date."""
        perms, owner = get_corporationowner_or_none(
            request=request, corporation_id=corporation_id
        )

        if owner is None:
            return HTTPStatus.NOT_FOUND, {
                "error": _("Corporation not found in Ledger.")
            }

        if perms is False:
            return HTTPStatus.FORBIDDEN, {
                "error": _("You do not have permission to view this corporation.")
            }
        # pylint: disable=duplicate-code
        return self.create_entity_details(
            owner=owner,
            entity_id=entity_id,
            filters=filters,
            section=section,
        )
