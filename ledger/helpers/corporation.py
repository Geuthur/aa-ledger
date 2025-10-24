"""PvE Views"""

# Standard Library
from decimal import Decimal
from typing import Any

# Django
from django.db.models import DecimalField, Q, QuerySet, Sum
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.constants import NPC_ENTITIES
from ledger.helpers.billboard import BillboardSystem
from ledger.helpers.core import LedgerCore, LedgerEntity
from ledger.helpers.ref_type import RefTypeManager
from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CorporationData(LedgerCore):
    """Class to hold character data for the ledger."""

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        corporation: CorporationAudit,
        division_id: int = None,
        year: int = None,
        month: int = None,
        day: int = None,
        section: str = None,
    ):
        super().__init__(year, month, day)
        self.corporation = corporation
        self.entity_id = corporation.corporation.corporation_id
        self.division_id = division_id
        self.section = section
        self.auth_char_ids = self.auth_character_ids
        self.billboard = BillboardSystem()
        self.queryset = (
            self._get_journal_queryset()
        )  # Prepare Queryset and auxiliary data

    @property
    def has_data(self) -> bool:
        """Return True if there is data for the corporation in the selected date range."""
        return self.queryset.exists()

    @property
    def activity_years(self) -> list[int]:
        """Return a list of years with data for the corporation."""
        return (
            CorporationWalletJournalEntry.objects.filter(
                division__corporation=self.corporation
            )
            .values_list("date__year", flat=True)
            .distinct()
            .order_by("-date__year")
        )

    @property
    def divisions(self) -> QuerySet:
        """Return a list of divisions for the corporation."""
        return CorporationWalletDivision.objects.filter(
            corporation=self.corporation
        ).order_by("division_id")

    def _get_journal_queryset(self) -> QuerySet[CorporationWalletJournalEntry]:
        """Return the base queryset filtered by the current date range and corporation division."""
        if self.division_id is not None:
            return CorporationWalletJournalEntry.objects.filter(
                self.filter_date,
                division__corporation=self.corporation,
                division=self.division_id,
            ).exclude(
                first_party_id=self.corporation.corporation.corporation_id,
                second_party_id=self.corporation.corporation.corporation_id,
            )
        return CorporationWalletJournalEntry.objects.filter(
            self.filter_date,
            division__corporation=self.corporation,
        ).exclude(
            first_party_id=self.corporation.corporation.corporation_id,
            second_party_id=self.corporation.corporation.corporation_id,
        )

    def _compute_entities(
        self, journal: QuerySet[CorporationWalletJournalEntry]
    ) -> set:
        """Return a set of all entity IDs (first and second parties) present in the current journal."""
        return set(journal.values_list("second_party_id", flat=True)) | set(
            journal.values_list("first_party_id", flat=True)
        )

    # pylint: disable=duplicate-code
    def _compute_journal_values(
        self, journal: QuerySet[CorporationWalletJournalEntry]
    ) -> QuerySet[dict[str, Any]]:
        """Return the journal values for the current journal."""
        return journal.values(
            "first_party_id", "second_party_id", "pk", "ref_type"
        ).annotate(
            bounty=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeManager.BOUNTY_PRIZES),
                output_field=DecimalField(),
            ),
            ess=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeManager.ESS_TRANSFER),
                output_field=DecimalField(),
            ),
            costs=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeManager.all_ref_types(), amount__lt=0),
                output_field=DecimalField(),
            ),
            miscellaneous=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeManager.all_ref_types(), amount__gt=0),
                output_field=DecimalField(),
            ),
        )

    def create_entity_data(
        self,
        entity: LedgerEntity,
        alts: EveCharacter = None,
    ) -> dict:
        """Create the URL for entity details based on the view type."""
        ids = (
            list(alts.values_list("character__character_id", flat=True))
            if alts is not None
            else [entity.entity_id]
        )

        # Create Alts Dictionary
        alts_dict = {}
        if alts is not None:
            for alt in alts:
                alts_dict[alt.character.character_id] = alt.character.character_name

            # Remove the main character from the alts dictionary only one entry
            if len(alts_dict) == 1:
                alts_dict.pop(entity.entity_id, None)

        used_pks = set()
        bounty = Decimal(0)
        ess = Decimal(0)
        miscellaneous = Decimal(0)
        costs = Decimal(0)

        for pk, rows in list(self.entries.items()):
            for row in rows:
                if row["first_party_id"] in ids or row["second_party_id"] in ids:
                    if RefTypeManager.special_cases(
                        row, ids=ids, account_char_ids=self.auth_char_ids
                    ):
                        continue
                    bounty += row.get("bounty") or Decimal(0)
                    ess += row.get("ess") or Decimal(0)
                    miscellaneous += row.get("miscellaneous") or Decimal(0)
                    costs += row.get("costs") or Decimal(0)
                    used_pks.add(pk)

        # Remove Used Pks from Entries
        # This is to prevent the entries from being used in the future
        for pk in used_pks:
            self.entries.pop(pk, None)

        total = sum([bounty, ess, miscellaneous, costs])

        if total == 0:
            return None

        char_data = {
            "entity": entity,
            "alts": alts_dict,
            "ledger": {
                "bounty": bounty,
                "ess": ess,
                "miscellaneous": miscellaneous,
                "costs": costs,
                "total": total,
            },
            "type": entity.type,
        }

        return char_data

    def generate_ledger_data(self) -> dict:
        """
        Generate the ledger data for the corporation.

        This method processes the journal entries, builds the ledger data,
        and prepares the context for rendering the corporation ledger view.
        """
        # Compute all entities in the journal
        self.entities = self._compute_entities(self.queryset)
        # Compute journal values
        journal = self._compute_journal_values(self.queryset)

        # Caching
        ledger_hash = self.get_ledger_journal_hash(journal.values_list("pk"))
        cache_key = f"{self.corporation.corporation.corporation_id}_{self.division_id}"

        # Get Cached Data if available
        ledger, finished_entities = self.get_cache_ledger(
            ledger_hash=ledger_hash, cache_key=cache_key
        )

        if finished_entities is False or ledger is False:
            # Build the entries from the journal
            self.entries = {}
            for row in journal:
                self.entries.setdefault(row["pk"], []).append(row)

            # Process Auth Accounts first
            ledger, finished_entities = self._process_auth_accounts()
            # Process remaining entities
            ledger, finished_entities = self._process_remaining_entities(
                ledger, finished_entities
            )
            # Process corporation entity last to ensure it's always included
            self._handle_entity(
                ledger=ledger,
                entity_id=self.corporation.corporation.corporation_id,
                corporation_obj=self.corporation.corporation,
            )

            # Create Cache
            self.set_cache_ledger(
                ledger_hash=ledger_hash,
                cache_key=cache_key,
                ledger=ledger,
                finished_entities=finished_entities,
            )

        # Finalize the billboard for the ledger.
        self.billboard.change_view(self.get_view_mode())
        self.create_rattingbar(journal=journal, entities_ids=list(finished_entities))
        self.create_chord(ledger)
        return ledger

    def generate_data_export(self) -> dict:
        """Generate the data export for the corporation."""
        # Compute all entities in the journal
        self.entities = self._compute_entities(self.queryset)
        # Compute journal values
        journal = self._compute_journal_values(self.queryset)

        # Build the entries from the journal
        self.entries = {}
        for row in journal:
            self.entries.setdefault(row["pk"], []).append(row)

        # Process Auth Accounts first
        ledger, finished_entities = self._process_auth_accounts()
        # Process remaining entities
        ledger, finished_entities = self._process_remaining_entities(
            ledger, finished_entities
        )
        # Process corporation entity last to ensure it's always included
        self._handle_entity(
            ledger=ledger,
            entity_id=self.corporation.corporation.corporation_id,
            corporation_obj=self.corporation.corporation,
        )
        return ledger

    # pylint: disable=too-many-arguments
    def _handle_entity(
        self,
        ledger: list,
        entity_id: int,
        character_obj=None,
        corporation_obj=None,
        alts=None,
        add_finished: bool = True,
        finished_ids=None,
    ) -> set:
        """Create entity object, add to ledger if it has data and return IDs to mark finished.

        - ledger: list to append to
        - entity_id: numeric id
        - character_obj / corporation_obj: optional objects to attach to LedgerEntity
        - alts: optional alts queryset passed to create_entity_data
        - add_finished: whether to return ids that should be added to finished_entities
        - finished_ids: explicit IDs (set or iterable) to mark finished (used for accounts)
        """
        details_url = self.create_url(
            viewname="corporation_details",
            corporation_id=self.corporation.corporation.corporation_id,
            entity_id=entity_id,
            section="single",
        )
        entity_obj = LedgerEntity(
            entity_id,
            character_obj=character_obj,
            corporation_obj=corporation_obj,
            details_url=details_url,
        )

        # Create the character data for the ledger
        char_data = self.create_entity_data(entity=entity_obj, alts=alts)

        # Only add to ledger if there is data
        if char_data is None:
            return set()

        ledger.append(char_data)

        if not add_finished:
            return set()

        if finished_ids is not None:
            return set(finished_ids)

        return {entity_id}

    def _process_auth_accounts(self):
        """Process Auth Account information for the ledger."""
        ledger = []
        finished_entities = set()
        for account in self.auth_accounts:
            alts = account.user.character_ownerships.all()
            existing_alts = set(
                alts.values_list("character__character_id", flat=True)
            ).intersection(self.entities)
            alts = alts.filter(character__character_id__in=existing_alts)
            if not existing_alts:
                continue
            finished_entities.update(
                self._handle_entity(
                    ledger,
                    account.main_character.character_id,
                    character_obj=account.main_character,
                    alts=alts,
                    finished_ids=existing_alts,
                )
            )
        return ledger, finished_entities

    def _process_remaining_entities(self, ledger, finished_entities: set):
        """Process remaining entities for the ledger."""
        remaining_entities = self.entities - finished_entities

        # If no remaining entities, return finished_entities
        if not remaining_entities:
            return ledger, finished_entities

        for entity_id in remaining_entities:
            if entity_id in NPC_ENTITIES:
                continue
            if entity_id == self.corporation.corporation.corporation_id:
                continue
            finished_entities.update(self._handle_entity(ledger, entity_id))
        return ledger, finished_entities

    def create_rattingbar(
        self,
        journal: QuerySet[CorporationWalletJournalEntry],
        entities_ids: list = None,
    ):
        """Create the ratting bar for the view."""
        if not entities_ids:
            return

        # Create the timeline for the ratting bar
        rattingbar_timeline = self.billboard.create_timeline(journal)
        # Annotate the timeline with the relevant data
        rattingbar = (
            rattingbar_timeline.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
        )
        # Generate the XY series for the ratting bar
        self.billboard.create_or_update_results(rattingbar)
        series, categories = self.billboard.generate_xy_series()
        if series and categories:
            # Create the ratting bar chart
            self.billboard.create_xy_chart(
                title=_("Ratting Bar"), categories=categories, series=series
            )

    def create_chord(self, ledger_data: list[dict]):
        """Create the chord chart for the view."""
        if not ledger_data:
            return

        for entry in ledger_data:
            entity_name = entry["entity"].entity_name
            ledger = entry["ledger"]
            self.billboard.chord_add_data(
                chord_from=entity_name,
                chord_to=_("Bounty (Wallet)"),
                value=ledger.get("bounty", 0),
            )
            self.billboard.chord_add_data(
                chord_from=entity_name,
                chord_to=_("ESS (Wallet)"),
                value=ledger.get("ess", 0),
            )
            self.billboard.chord_add_data(
                chord_from=entity_name,
                chord_to=_("Costs (Wallet)"),
                value=abs(ledger.get("costs", 0)),
            )
            self.billboard.chord_add_data(
                chord_from=entity_name,
                chord_to=_("Miscellaneous (Wallet)"),
                value=abs(ledger.get("miscellaneous", 0)),
            )
        self.billboard.chord_handle_overflow()
