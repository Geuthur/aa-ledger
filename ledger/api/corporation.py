# Standard Library
from collections import defaultdict
from decimal import Decimal

# Third Party
from ninja import NinjaAPI, Schema

# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.api.helpers.core import (
    get_corporationowner_or_none,
)
from ledger.api.helpers.icons import (
    get_corporation_details_info_button,
    get_corporation_ledger_popover_button,
    get_ref_type_details_popover_button,
)
from ledger.api.schema import (
    BillboardSchema,
    CategorySchema,
    CorporationLedgerRequestInfo,
    EntitySchema,
    LedgerDetailsResponse,
    LedgerDetailsSummary,
    LedgerResponse,
    LedgerSchema,
    OwnerSchema,
)
from ledger.constants import NPC_ENTITIES
from ledger.helpers.billboard import BillboardSystem
from ledger.helpers.cache import CacheManager
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
    actions: str = ""


class CorporationLedgerResponse(LedgerResponse):
    """
    Schema for Corporation Ledger Response.

    This schema represents the response structure for corporation ledger data,
    extending the base :class:`LedgerResponse` to include corporation-specific ledger data.

    Attributes:
        information (CorporationLedgerRequestInfo): The request information for the corporation ledger.
        entities (list[LedgerEntitySchema]): The list of ledger entities.

    """

    information: CorporationLedgerRequestInfo
    entities: list[LedgerEntitySchema]


class CorporationApiEndpoints:
    tags = ["Corporation"]

    # pylint: disable=duplicate-code
    def _create_datatable_footer(
        self,
        entities: list[LedgerEntitySchema],
        request_info: CorporationLedgerRequestInfo,
    ) -> CorporationLedgerRequestInfo:
        """
        Create the footer HTML for the Ledger datatable.

        This Helper function creates the footer HTML for the Ledger datatable
        by summing up the respective fields from the list of entities.

        Args:
            entities (list[LedgerEntitySchema]): The list of entity ledger data.

        Returns:
            str: The generated footer HTML.
        """
        total_bounty = sum(entity.ledger.bounty for entity in entities)
        total_ess = sum(entity.ledger.ess for entity in entities)
        total_costs = sum(entity.ledger.costs for entity in entities)
        total_miscellaneous = sum(entity.ledger.miscellaneous for entity in entities)
        total_total = sum(entity.ledger.total for entity in entities)

        # Generate Details Link
        url = get_corporation_details_info_button(
            entity_id=request_info.owner_id,
            request_info=request_info,
        )

        # Skip Footer if no Totals
        if total_total == 0:
            return ""

        footer_html = f"""
            <tr>
                <th class="border-top">{_("Summary")}</th>
                <th class="border-top text-end">{intcomma(value=int(total_bounty), use_l10n=True)} ISK</th>
                <th class="border-top text-end">{intcomma(value=int(total_ess), use_l10n=True)} ISK</th>
                <th class="border-top text-end">{intcomma(value=int(total_miscellaneous), use_l10n=True)} ISK</th>
                <th class="border-top text-end">{intcomma(value=int(total_costs), use_l10n=True)} ISK</th>
                <th class="border-start border-top text-end">{intcomma(value=int(total_total), use_l10n=True)} ISK</th>
                <th class="border-top">{url}</th>
            </tr>
        """
        request_info.footer_html = footer_html
        return request_info

    def _sum_by_ref_types(
        self, entry_list: list[dict], ref_types: list[str], sign: str | None = None
    ) -> Decimal:
        """Helper function to sum amounts in entry_list filtered by ref_types and sign.

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

    # pylint: disable=too-many-locals
    def _process_entity_entries(
        self,
        entity: EntitySchema,
        request_info: CorporationLedgerRequestInfo,
        entries_by_entity: dict[int, list[dict]],
        processed_entry_ids: set[int] | None = None,
    ) -> LedgerEntitySchema | None:
        """
        Process the entity entries for the corporation owner.

        This Helper function processes the entity entries for the corporation
        based on the provided date query.

        Args:
            owner (CorporationOwner): The corporation owner object.
            request_info (LedgerRequestInfo): The request information object.
        Returns:
            list[EntitySchema]: A list of entity schemas for each processed entity.
        """
        # Build combined entry list for primary entity and any alt_ids
        combined_entries: list[dict] = []
        combined_entries.extend(entries_by_entity.get(entity.entity_id, []))

        # Initialize processed ids set if not provided
        if processed_entry_ids is None:
            processed_entry_ids = set()

        # If this EntitySchema carries alt_ids (members), include those rows too
        alt_ids = getattr(entity, "alt_ids", None) or []
        for aid in alt_ids:
            combined_entries.extend(entries_by_entity.get(aid, []))

        # Filter out already processed entries
        entry_list = [
            r for r in combined_entries if r.get("entry_id") not in processed_entry_ids
        ]

        # Skip Entity if no Ledger Entries
        if not entry_list:
            # logger.debug(f"Skipping Entity {entity} - No Ledger Entries")
            return None

        # Deduplicate by entry_id (an entry may appear under multiple alt_ids)
        unique: dict[int, dict] = {}
        for r in entry_list:
            unique[r["entry_id"]] = r

        # Collect Entry IDs to Mark as Processed
        entry_ids = list(unique.keys())
        entry_list = list(unique.values())

        # Aggregate Data using in-memory rows
        entity_bounty = self._sum_by_ref_types(entry_list, RefTypeManager.BOUNTY_PRIZES)
        entity_ess = self._sum_by_ref_types(entry_list, RefTypeManager.ESS_TRANSFER)
        entity_costs = self._sum_by_ref_types(
            entry_list, RefTypeManager.ledger_ref_types(), sign="negative"
        )
        entity_miscellaneous = self._sum_by_ref_types(
            entry_list, RefTypeManager.ledger_ref_types(), sign="positive"
        )

        total = sum(
            [
                entity_bounty,
                entity_ess,
                entity_miscellaneous,
                entity_costs,
            ]
        )

        response_entity = LedgerEntitySchema(
            entity=entity,
            ledger=LedgerSchema(
                bounty=entity_bounty,
                ess=entity_ess,
                costs=entity_costs,
                miscellaneous=entity_miscellaneous,
                total=total,
            ),
            actions=get_corporation_details_info_button(
                entity_id=entity.entity_id, request_info=request_info, section="single"
            ),
        )
        # Mark these entries as processed so they won't be used again
        processed_entry_ids.update(entry_ids)
        return response_entity

    # pylint: disable=too-many-positional-arguments
    def process_member_ledger_data(
        self,
        entity_ids: set[int],
        request_info: CorporationLedgerRequestInfo,
        entries_by_entity: dict[int, list[dict]],
        processed_entry_ids: set[int],
        entity_ledger_list: list[LedgerEntitySchema],
    ) -> list[EntitySchema]:
        """
        Process the ledger data for auth member entities.

        This Helper function processes the ledger data for auth member entities
        based on the provided date query.

        Args:
            entity_ids (set[int]): The set of entity IDs to process.
            entries_by_entity (dict[int, list[dict]]): The mapping of entity IDs to their ledger entries.
            processed_entry_ids (set[int]): The set of already processed ledger entry IDs.
            entity_ledger_list (list[LedgerEntitySchema]): The list to append processed ledger data to.
        Returns:
            list[int]: A list of processed entity IDs.
        """

        accounts = UserProfile.objects.filter(
            main_character__isnull=False,
        ).order_by(
            "user__profile__main_character__character_name",
        )

        auth_entity_ids = []
        for account in accounts:
            alts = account.user.character_ownerships.all()
            existings_alts = alts.filter(
                character__character_id__in=entity_ids.intersection(
                    alts.values_list("character__character_id", flat=True)
                )
            )
            alt_ids = list(
                existings_alts.values_list("character__character_id", flat=True)
            )

            # Skip if no characters in Corporation
            if not alt_ids:
                continue

            response_ledger = self._process_entity_entries(
                entity=EntitySchema(
                    entity_id=account.main_character.character_id,
                    entity_name=account.main_character.character_name,
                    alt_ids=alt_ids,
                    icon=get_character_portrait_url(
                        character_id=account.main_character.character_id,
                        character_name=account.main_character.character_name,
                        size=32,
                        as_html=True,
                    ),
                    popover=get_corporation_ledger_popover_button(alts=existings_alts),
                ),
                request_info=request_info,
                entries_by_entity=entries_by_entity,
                processed_entry_ids=processed_entry_ids,
            )
            auth_entity_ids.extend(alt_ids)
            if response_ledger is None:
                continue
            # Add Entity Ledger to List
            entity_ledger_list.append(response_ledger)
        return auth_entity_ids

    # pylint: disable=too-many-positional-arguments
    def _process_ledger_data(
        self,
        entities: list[EveEntity],
        request_info: CorporationLedgerRequestInfo,
        entries_by_entity: dict[int, list[dict]],
        processed_entry_ids: set[int],
        entity_ledger_list: list[LedgerEntitySchema],
    ) -> list[LedgerEntitySchema]:
        """
        Process the ledger data for the given entity IDs.

        This Helper function processes the ledger data for the given entity IDs
        based on the provided date query.

        Args:
            entity_ids (list[int]): The list of entity IDs to process.
            entries_by_entity (dict[int, list[dict]]): The mapping of entity IDs to their ledger entries.
            processed_entry_ids (set[int]): The set of already processed ledger entry IDs.
            entity_ledger_list (list[LedgerEntitySchema]): The list to append processed ledger data to.
        Returns:
            list[LedgerEntitySchema]: A list of ledger responses for each entity.
        """
        for entity in entities:
            response_ledger = self._process_entity_entries(
                entity=EntitySchema(
                    entity_id=entity.eve_id,
                    entity_name=entity.name,
                    icon=entity.get_portrait(size=32, as_html=True),
                ),
                request_info=request_info,
                entries_by_entity=entries_by_entity,
                processed_entry_ids=processed_entry_ids,
            )
            if response_ledger is None:
                continue
            # Add Entity Ledger to List
            entity_ledger_list.append(response_ledger)

        return entity_ledger_list

    # pylint: disable=too-many-locals
    def generate_entity_data(
        self, owner: CorporationOwner, request_info: CorporationLedgerRequestInfo
    ) -> list[CorporationLedgerResponse]:
        """
        Generate the ledger data for a corporation owner.

        This Helper function generates the ledger data for a entity
        based on the provided date query.

        Args:
            owner (CorporationOwner): The corporation owner object.
            request_info (LedgerRequestInfo): The request information object.
        Returns:
            list[CorporationLedgerResponse]: A list of ledger responses for each entity.
        """
        # Get Corporation Wallet Journal Entries
        corp_journal_values = (
            CorporationWalletJournalEntry.objects.filter(
                division__corporation=owner,
                **request_info.to_date_query(),
                **request_info.to_division_query(),
            )
            # Exclude Zero Amount Entries
            .exclude(amount=Decimal("0.00"))
            # Exclude Internal Transfers
            .exclude(
                first_party_id=owner.eve_corporation.corporation_id,
                second_party_id=owner.eve_corporation.corporation_id,
            )
            .values(
                "entry_id",
                "amount",
                "ref_type",
                "first_party_id",
                "second_party_id",
                "date",
            )
            .order_by("-date")
        )

        header_ids = list(corp_journal_values.values_list("entry_id", flat=True))

        # Skip Corporation if no Ledger Entries
        if len(header_ids) == 0:
            return []

        # Add Owner ID to header ids to ensure uniqueness
        header_ids.append(owner.eve_corporation.corporation_id)

        # Create Ledger Hash
        wallet_journal_hash = self.cache_manager.create_ledger_hash(header_ids)

        # Get Cached Ledger if Available
        entity_ledger_list = self.cache_manager.get_cache_ledger(
            ledger_hash=wallet_journal_hash
        )
        if entity_ledger_list is False:
            entity_ids = set()
            entity_ledger_list: list[LedgerEntitySchema] = []
            processed_entry_ids: set[int] = set()
            entries_by_entity: dict[int, list[dict]] = defaultdict(list)

            for row in corp_journal_values:
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
                request_info=request_info,
                entries_by_entity=entries_by_entity,
                processed_entry_ids=processed_entry_ids,
                entity_ledger_list=entity_ledger_list,
            )

            # Process Remaining Entities
            entities = (
                EveEntity.objects.filter(eve_id__in=entity_ids)
                # Exclude Auth Entities
                .exclude(eve_id__in=auth_entity_ids)
                # Exclude NPC Entities
                .exclude(eve_id__in=NPC_ENTITIES)
                # Exclude Corporation Itself
                .exclude(eve_id=owner.eve_corporation.corporation_id).order_by("name")
            )

            # Process NPC Entities Last
            npc_entities = EveEntity.objects.filter(eve_id__in=NPC_ENTITIES).order_by(
                "name"
            )

            # Process each Entity
            self._process_ledger_data(
                entities=list(entities),
                request_info=request_info,
                entries_by_entity=entries_by_entity,
                processed_entry_ids=processed_entry_ids,
                entity_ledger_list=entity_ledger_list,
            )

            # Process NPC Entities
            self._process_ledger_data(
                entities=list(npc_entities),
                request_info=request_info,
                entries_by_entity=entries_by_entity,
                processed_entry_ids=processed_entry_ids,
                entity_ledger_list=entity_ledger_list,
            )
            # Cache Ledger Response
            self.cache_manager.set_cache_ledger(
                ledger_hash=wallet_journal_hash,
                ledger_data=entity_ledger_list,
            )
        return entity_ledger_list

    def generate_billboard_data(
        self,
        owner: CorporationOwner,
        entity_ledger_list: list[LedgerEntitySchema],
        request_info: CorporationLedgerRequestInfo,
    ) -> BillboardSchema:
        """
        Generate the billboard data for the corporation ledger.

        This Helper function generates the billboard data for the corporation
        based on the provided character ledger data.

        Args:
            owner (CorporationOwner): The corporation owner object.
            character_ledger_list (list[LedgerCharacterSchema]): The list of character ledger data.
            request_info (LedgerRequestInfo): The request information object.
        Returns:
            BillboardSchema: The generated billboard data.
        """
        billboard = BillboardSystem()

        # Get Wallet Journal Entries
        corp_wallet_journal = (
            CorporationWalletJournalEntry.objects.filter(
                division__corporation=owner,
                **request_info.to_date_query(),
                **request_info.to_division_query(),
            )
            # Exclude Zero Amount Entries
            .exclude(amount=Decimal("0.00"))
            # Exclude Internal Transfers
            .exclude(
                first_party_id=owner.eve_corporation.corporation_id,
                second_party_id=owner.eve_corporation.corporation_id,
            )
        )

        # Get IDs for Hashing
        header_ids = list(corp_wallet_journal.values_list("entry_id", flat=True))

        # add corporation id to header ids to ensure uniqueness
        header_ids.append(owner.eve_corporation.corporation_id)

        # Skip Corporation if no Ledger Entries
        if len(header_ids) == 0:
            return BillboardSchema()

        # Create Ledger Hash
        wallet_journal_hash = self.cache_manager.create_ledger_hash(header_ids)

        # Get Cached Billboard if Available
        response_billboard = self.cache_manager.get_cache_billboard(
            billboard_hash=wallet_journal_hash
        )
        if response_billboard is False:
            logger.debug(f"Billboard Cache for: {owner}")
            # Create Timelines
            wallet_timeline = (
                billboard.create_timeline(corp_wallet_journal)
                .annotate_bounty_income()
                .annotate_ess_income()
                .annotate_miscellaneous()
            )

            # Generate the billboard data
            billboard.create_or_update_results(wallet_timeline)

            # Generate XY Series
            series, categories = billboard.generate_xy_series()
            if series and categories:
                billboard.create_xy_chart(
                    title=_("Ratting Income Over Time"),
                    categories=categories,
                    series=series,
                )

            # Generate Chord Data
            for entity_data in entity_ledger_list:
                bounty = entity_data.ledger.bounty
                ess = entity_data.ledger.ess
                miscellaneous = entity_data.ledger.miscellaneous
                costs = entity_data.ledger.costs

                billboard.chord_add_data(
                    chord_from=entity_data.entity.entity_name,
                    chord_to=_("Bounty"),
                    value=abs(bounty),
                )
                billboard.chord_add_data(
                    chord_from=entity_data.entity.entity_name,
                    chord_to=_("ESS"),
                    value=abs(ess),
                )
                billboard.chord_add_data(
                    chord_from=entity_data.entity.entity_name,
                    chord_to=_("Miscellaneous"),
                    value=abs(miscellaneous),
                )
                billboard.chord_add_data(
                    chord_from=entity_data.entity.entity_name,
                    chord_to=_("Costs"),
                    value=abs(costs),
                )

            # Handle Chord Overflow
            billboard.chord_handle_overflow()

            response_billboard = BillboardSchema(
                xy_chart=billboard.dict.rattingbar,
                chord_chart=billboard.dict.charts,
            )
            # Cache Billboard Response
            self.cache_manager.set_cache_billboard(
                billboard_hash=wallet_journal_hash,
                billboard_data=response_billboard,
            )
        # Billboard Data Generation Logic Here
        return response_billboard

    # pylint: disable=too-many-positional-arguments, duplicate-code
    def _ledger_api_response(
        self,
        request,
        corporation_id: int,
        year: int,
        division_id: int = None,
        month: int = None,
        day: int = None,
    ) -> CorporationLedgerResponse | tuple[int, dict]:
        """
        Helper function to generate ledger response for various date parameters.

        This function consolidates the common logic for generating the ledger response
        based on the provided date parameters (year, month, day) and section.

        Args:
            request (WSGIRequest): The incoming request object.
            corporation_id (int): The corporation ID.
            year (int): The year for the ledger data.
            month (int, optional): The month for the ledger data. Defaults to None.
            day (int, optional): The day for the ledger data. Defaults to None.
            section (str): The section type ('single' or 'summary').

        Returns:
            CorporationLedgerResponse | tuple[int, dict]: The ledger response or error tuple.
        """
        perms, owner = get_corporationowner_or_none(
            request=request, corporation_id=corporation_id
        )

        if owner is None:
            return 404, {"error": _("Corporation not found in Ledger.")}

        if perms is False:
            return 403, {
                "error": _("You do not have permission to view this corporation.")
            }

        # Build Request Info
        request_info = CorporationLedgerRequestInfo(
            owner_id=owner.eve_corporation.corporation_id,
            division_id=division_id,
            year=year,
            month=month,
            day=day,
        )

        # Generate Entity Ledger Data
        entity_ledger_list = self.generate_entity_data(
            owner=owner,
            request_info=request_info,
        )

        # Generate Billboard Data
        billboard = self.generate_billboard_data(
            owner=owner,
            entity_ledger_list=entity_ledger_list,
            request_info=request_info,
        )

        # Update Request Info with Available Data
        self._create_datatable_footer(
            entities=entity_ledger_list, request_info=request_info
        )

        response_ledger = CorporationLedgerResponse(
            owner=OwnerSchema(
                character_id=owner.eve_corporation.corporation_id,
                character_name=owner.eve_corporation.corporation_name,
                icon=owner.get_portrait(as_html=True),
            ),
            information=request_info,
            entities=entity_ledger_list,
            billboard=billboard,
            actions=get_corporation_details_info_button(
                entity_id=owner.eve_corporation.corporation_id,
                request_info=request_info,
            ),
        )

        return response_ledger

    # pylint: disable=too-many-statements, function-redefined, duplicate-code
    # flake8: noqa: F811
    def __init__(self, api: NinjaAPI):
        self.cache_manager = CacheManager()

        @api.get(
            "corporation/{corporation_id}/division/{division_id}/date/{year}/",
            response={200: CorporationLedgerResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_corporation_ledger(
            request: WSGIRequest, corporation_id: int, division_id: int, year: int
        ):
            """Get the ledger for a character for a specific year. Admin Endpoint."""
            return self._ledger_api_response(
                request=request,
                corporation_id=corporation_id,
                division_id=division_id,
                year=year,
            )

        @api.get(
            "corporation/{corporation_id}/division/{division_id}/date/{year}/{month}/",
            response={200: CorporationLedgerResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_corporation_ledger(
            request: WSGIRequest,
            corporation_id: int,
            division_id: int,
            year: int,
            month: int,
        ):
            """Get the ledger for a character for a specific year. Admin Endpoint."""
            return self._ledger_api_response(
                request=request,
                corporation_id=corporation_id,
                division_id=division_id,
                year=year,
                month=month,
            )

        @api.get(
            "corporation/{corporation_id}/division/{division_id}/date/{year}/{month}/{day}/",
            response={200: CorporationLedgerResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_corporation_ledger(
            request: WSGIRequest,
            corporation_id: int,
            division_id: int,
            year: int,
            month: int,
            day: int,
        ):
            """Get the ledger for a character for a specific year. Admin Endpoint."""
            return self._ledger_api_response(
                request=request,
                corporation_id=corporation_id,
                division_id=division_id,
                year=year,
                month=month,
                day=day,
            )

        @api.get(
            "corporation/{corporation_id}/date/{year}/",
            response={200: CorporationLedgerResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_corporation_ledger(
            request: WSGIRequest, corporation_id: int, year: int
        ):
            """Get the ledger for a character for a specific year. Admin Endpoint."""
            return self._ledger_api_response(
                request=request,
                corporation_id=corporation_id,
                year=year,
            )

        @api.get(
            "corporation/{corporation_id}/date/{year}/{month}/",
            response={200: CorporationLedgerResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_corporation_ledger(
            request: WSGIRequest, corporation_id: int, year: int, month: int
        ):
            """Get the ledger for a character for a specific year. Admin Endpoint."""
            return self._ledger_api_response(
                request=request,
                corporation_id=corporation_id,
                year=year,
                month=month,
            )

        @api.get(
            "corporation/{corporation_id}/date/{year}/{month}/{day}/",
            response={200: CorporationLedgerResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        # pylint: disable=too-many-positional-arguments
        def get_corporation_ledger(
            request: WSGIRequest,
            corporation_id: int,
            year: int,
            month: int,
            day: int,
        ):
            """Get the ledger for a character for a specific year. Admin Endpoint."""
            return self._ledger_api_response(
                request=request,
                corporation_id=corporation_id,
                year=year,
                month=month,
                day=day,
            )


class CorporationDetailsApiEndpoints:
    tags = ["Corporation Details"]

    # pylint: disable=duplicate-code
    def _create_datatable_footer(self, value: float) -> str:
        """Create the footer HTML for the datatable."""
        footer_html = f"""
            <tr>
                <th>{_('Summary')}</th>
                <th class="text-end">{intcomma(value=int(value), use_l10n=True)} ISK</th>
                <th></th>
            </tr>
        """
        return footer_html

    # pylint: disable=too-many-locals, too-many-positional-arguments
    def _create_ledger_details(
        self,
        journal: QuerySet[CorporationWalletJournalEntry],
        request_info: CorporationLedgerRequestInfo,
    ) -> LedgerDetailsResponse:
        """
        Generate the detailed ledger data for a character.
        This Helper function generates the detailed ledger data for a character
        based on the provided date query.

        Args:
            journal (QuerySet): The wallet journal entries.
            mining (QuerySet): The mining ledger entries. Defaults to None.
            request_info (LedgerRequestInfo): The request information containing date and section details.
        Returns:
            LedgerDetailsResponse: The generated ledger details response.
        """
        ref_types = RefTypeManager.get_all_categories()

        avg = request_info.day if request_info.day else timezone.now().day
        if request_info.section == "summary":
            avg = 365

        monthly_list = []
        daily_list = []
        hourly_list = []
        summary = 0
        # Income/Cost Ref Types
        for ref_type, value in ref_types.items():
            ref_type_name = ref_type.lower()
            for kind, income_flag in (("income", True), ("cost", False)):
                kwargs = {"ref_type": value, "income": income_flag}
                amount = journal.aggregate_ref_type(**kwargs)
                if (income_flag and amount > 0) or (not income_flag and amount < 0):
                    monthly = CategorySchema(
                        name=_(
                            f"{ref_type_name.replace('_', ' ').title()} {kind.capitalize()}"
                        ),
                        amount=amount,
                        average=amount / avg / 30,
                        average_tick=amount / avg / 30 / 20,
                        ref_types=get_ref_type_details_popover_button(ref_types=value),
                    )

                    daily = CategorySchema(
                        name=_(
                            f"{ref_type_name.replace('_', ' ').title()} {kind.capitalize()}"
                        ),
                        amount=amount / avg,
                        average=amount / avg / 30,
                        average_tick=amount / avg / 20,
                        ref_types=get_ref_type_details_popover_button(ref_types=value),
                    )

                    hourly = CategorySchema(
                        name=_(
                            f"{ref_type_name.replace('_', ' ').title()} {kind.capitalize()}"
                        ),
                        amount=amount / avg / 24,
                        average=amount / avg / 24 / 30,
                        average_tick=amount / avg / 24 / 20,
                        ref_types=get_ref_type_details_popover_button(ref_types=value),
                    )
                    # Add Amounts
                    summary += amount
                    monthly_list.append(monthly)
                    daily_list.append(daily)
                    hourly_list.append(hourly)

        if summary == 0:
            return None

        return LedgerDetailsResponse(
            summary=monthly_list,
            daily=daily_list,
            hourly=hourly_list,
            total=LedgerDetailsSummary(
                summary=self._create_datatable_footer(summary),
                daily=self._create_datatable_footer(
                    summary / avg,
                ),
                hourly=self._create_datatable_footer(
                    summary / avg / 24,
                ),
            ),
        )

    def _check_auth_account(
        self,
        owner: CorporationOwner,
        entity_id: int,
    ) -> list[int] | None:
        """
        Check if the entity_id belongs to a auth account of the corporation.
        """
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
        request_info: CorporationLedgerRequestInfo,
    ) -> dict:
        """
        Create the entity amounts for the Information View.
        """
        # Check if Entity is a Member
        alt_ids = self._check_auth_account(owner=owner, entity_id=entity_id)

        # Build Entity Query
        entity_query = Q(first_party_id=entity_id) | Q(second_party_id=entity_id)
        if alt_ids is not None:
            # If Member, query all alt_ids
            entity_query = Q(first_party_id__in=alt_ids) | Q(
                second_party_id__in=alt_ids
            )
        elif entity_id == owner.eve_corporation.corporation_id:
            # If Corporation itself query all entries
            entity_query = Q()

        # Get Wallet Journal Entries
        wallet_journal = (
            CorporationWalletJournalEntry.objects.filter(
                entity_query,
                division__corporation=owner,
                **request_info.to_date_query(),
                **request_info.to_division_query(),
            )
            # Exclude Zero Amount Entries
            .exclude(amount=Decimal("0.00"))
            # Exclude Internal Transfers
            .exclude(
                first_party_id=owner.eve_corporation.corporation_id,
                second_party_id=owner.eve_corporation.corporation_id,
            )
        )

        # If Member, Exclude Corporation Contracts (will count in Corporation itself)
        if alt_ids is not None:
            wallet_journal = wallet_journal.exclude(
                ref_type="contract_price_payment_corp",
                second_party_id__in=alt_ids,
            )

        response_ledger_details: LedgerDetailsResponse = self._create_ledger_details(
            journal=wallet_journal,
            request_info=request_info,
        )
        return response_ledger_details

    # pylint: disable=too-many-arguments
    def _ledger_details_api_response(
        self,
        request: WSGIRequest,
        corporation_id: int,
        entity_id: int,
        year: int,
        month: int = None,
        day: int = None,
        division_id: int = None,
        section: str = "summary",
    ):
        """
        Helper function to generate ledger details response for various date parameters.

        This function consolidates the common logic for generating the ledger details response
        based on the provided date parameters character_id, (year, month, day) and section.

        Args:
            request (WSGIRequest): The incoming request object.
            corporation_id (int): The corporation ID.
            entity_id (int): The entity ID.
            year (int): The year for the ledger data.
            month (int, optional): The month for the ledger data. Defaults to None.
            day (int, optional): The day for the ledger data. Defaults to None.
            division_id (int, optional): The division ID for the ledger data. Defaults to None.
            section (str): The section type ('single' or 'summary').
        Returns:
            LedgerDetailsResponse | tuple[int, dict]: The ledger details response or error tuple.
        """
        perms, owner = get_corporationowner_or_none(
            request=request, corporation_id=corporation_id
        )

        if owner is None:
            return 404, {"error": _("Corporation not found in Ledger.")}

        if perms is False:
            return 403, {
                "error": _("You do not have permission to view this corporation.")
            }

        request_info = CorporationLedgerRequestInfo(
            owner_id=owner.eve_corporation.corporation_id,
            entity_id=entity_id,
            division_id=division_id,
            year=year,
            month=month,
            day=day,
            section=section,
        )

        return self.create_entity_details(
            owner=owner,
            entity_id=entity_id,
            request_info=request_info,
        )

    # pylint: disable=too-many-statements, function-redefined, too-many-arguments
    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/division/{division_id}/date/{year}/section/{section}/view/details/{entity_id}/",
            response={200: LedgerDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_corporation_ledger_details(
            request: WSGIRequest,
            corporation_id: int,
            division_id: int,
            year: int,
            section: str,
            entity_id: int,
        ):
            return self._ledger_details_api_response(
                request=request,
                corporation_id=corporation_id,
                division_id=division_id,
                entity_id=entity_id,
                year=year,
                section=section,
            )

        @api.get(
            "corporation/{corporation_id}/division/{division_id}/date/{year}/{month}/section/{section}/view/details/{entity_id}/",
            response={200: LedgerDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_corporation_ledger_details(
            request: WSGIRequest,
            corporation_id: int,
            division_id: int,
            year: int,
            month: int,
            section: str,
            entity_id: int,
        ):
            return self._ledger_details_api_response(
                request=request,
                corporation_id=corporation_id,
                division_id=division_id,
                entity_id=entity_id,
                year=year,
                month=month,
                section=section,
            )

        @api.get(
            "corporation/{corporation_id}/division/{division_id}/date/{year}/{month}/{day}/section/{section}/view/details/{entity_id}/",
            response={200: LedgerDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_corporation_ledger_details(
            request: WSGIRequest,
            corporation_id: int,
            division_id: int,
            year: int,
            month: int,
            day: int,
            section: str,
            entity_id: int,
        ):
            return self._ledger_details_api_response(
                request=request,
                corporation_id=corporation_id,
                division_id=division_id,
                entity_id=entity_id,
                year=year,
                month=month,
                day=day,
                section=section,
            )

        @api.get(
            "corporation/{corporation_id}/date/{year}/section/{section}/view/details/{entity_id}/",
            response={200: LedgerDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_corporation_ledger_details(
            request: WSGIRequest,
            corporation_id: int,
            year: int,
            section: str,
            entity_id: int,
        ):
            return self._ledger_details_api_response(
                request=request,
                corporation_id=corporation_id,
                entity_id=entity_id,
                year=year,
                section=section,
            )

        @api.get(
            "corporation/{corporation_id}/date/{year}/{month}/section/{section}/view/details/{entity_id}/",
            response={200: LedgerDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_corporation_ledger_details(
            request: WSGIRequest,
            corporation_id: int,
            year: int,
            month: int,
            section: str,
            entity_id: int,
        ):
            return self._ledger_details_api_response(
                request=request,
                corporation_id=corporation_id,
                entity_id=entity_id,
                year=year,
                month=month,
                section=section,
            )

        @api.get(
            "corporation/{corporation_id}/date/{year}/{month}/{day}/section/{section}/view/details/{entity_id}/",
            response={200: LedgerDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_corporation_ledger_details(
            request: WSGIRequest,
            corporation_id: int,
            year: int,
            month: int,
            day: int,
            section: str,
            entity_id: int,
        ):
            return self._ledger_details_api_response(
                request=request,
                corporation_id=corporation_id,
                entity_id=entity_id,
                year=year,
                month=month,
                day=day,
                section=section,
            )
