"""PvE Views"""

# Standard Library
from decimal import Decimal
from typing import Any

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import DecimalField, F, Q, QuerySet, Sum
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.helpers.billboard import BillboardSystem
from ledger.helpers.core import LedgerCore, LedgerEntity
from ledger.helpers.ref_type import RefTypeManager
from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletJournalEntry,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class AllianceData(LedgerCore):
    """Class to hold alliance data for the ledger."""

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        alliance: EveAllianceInfo,
        request: WSGIRequest = None,
        year=None,
        month=None,
        day=None,
        section=None,
    ):
        super().__init__(year, month, day)
        self.request = request
        self.alliance = alliance
        self.entity_id = self.alliance.alliance_id
        self.section = section
        self.corporations = CorporationAudit.objects.filter(
            corporation__alliance__alliance_id=self.alliance.alliance_id
        ).values_list("corporation__corporation_id", flat=True)
        self.auth_char_ids = self.auth_character_ids
        self.billboard = BillboardSystem()
        self.queryset = (
            self._get_journal_queryset()
        )  # Base queryset filtered by date and alliance

    def _get_journal_queryset(self) -> QuerySet[CorporationWalletJournalEntry]:
        """Return the base queryset filtered by the current date range and corporation division."""
        return CorporationWalletJournalEntry.objects.filter(
            self.filter_date,
            division__corporation__corporation__alliance__alliance_id=self.alliance.alliance_id,
        ).exclude(
            Q(ref_type="corporation_account_withdrawal")
            & Q(first_party_id=F("second_party_id"))
        )

    def _compute_entities(
        self, journal: QuerySet[CorporationWalletJournalEntry]
    ) -> set:
        """Return a set of all entity IDs (first and second parties) present in the current journal."""
        return set(journal.values_list("second_party_id", flat=True)) | set(
            journal.values_list("first_party_id", flat=True)
        )

    def _compute_journal_values(
        self, journal: QuerySet[CorporationWalletJournalEntry]
    ) -> QuerySet[dict[str, Any]]:
        """Return the journal values for the current journal."""
        return journal.values(
            "first_party_id",
            "second_party_id",
            "pk",
            "ref_type",
            "division__corporation__corporation__corporation_id",
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

    # pylint: disable=duplicate-code
    def create_entity_data(
        self,
        entity: LedgerEntity,
    ) -> dict:
        """Create the URL for entity details based on the view type."""
        used_pks = set()
        bounty = Decimal(0)
        ess = Decimal(0)
        miscellaneous = Decimal(0)
        costs = Decimal(0)

        for pk, rows in list(self.entries.items()):
            for row in rows:
                if (
                    row["division__corporation__corporation__corporation_id"]
                    == entity.entity_id
                ):
                    if RefTypeManager.special_cases(
                        row, ids=[], account_char_ids=self.auth_char_ids
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

        misc = miscellaneous
        total = sum([bounty, ess, miscellaneous, costs])

        if total == 0:
            return None

        entity_ledger_info = {
            "entity": entity,
            "ledger": {
                "bounty": bounty,
                "ess": ess,
                "miscellaneous": misc,
                "costs": costs,
                "total": total,
            },
            "type": entity.type,
        }

        return entity_ledger_info

    # pylint: disable=duplicate-code
    def generate_ledger_data(self) -> dict:
        """Generate the ledger data for the alliance."""
        # Compute all entities in the journal
        self.entities = self._compute_entities(self.queryset)
        # Compute journal values
        journal = self._compute_journal_values(self.queryset)

        # Caching
        ledger_hash = self.get_ledger_journal_hash(journal.values_list("pk"))
        cache_key = f"{self.entity_id}"

        # Get Cached Data if available
        ledger, finished_entities = self.get_cache_ledger(
            ledger_hash=ledger_hash, cache_key=cache_key
        )

        if finished_entities is False or ledger is False:
            ledger = []
            finished_entities = set()

            # Build the entries from the journal
            self.entries = {}
            for row in journal:
                self.entries.setdefault(row["pk"], []).append(row)

            # Build Data for each corporation
            for corporation_id in self.corporations:
                # Create Details URL for the entity
                details_url = self.create_url(
                    viewname="corporation_details",
                    corporation_id=corporation_id,
                    entity_id=corporation_id,
                    section="summary",
                )

                # Create the LedgerEntity object for the entity
                entity_obj = LedgerEntity(
                    entity_id=corporation_id,
                    details_url=details_url,
                )

                corp_data = self.create_entity_data(
                    entity=entity_obj,
                )

                if corp_data is None:
                    continue

                ledger.append(corp_data)
                finished_entities.add(corporation_id)

            # Create Cache
            self.set_cache_ledger(
                ledger_hash=ledger_hash,
                cache_key=cache_key,
                ledger=ledger,
                finished_entities=finished_entities,
            )

        # Create the billboard data
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

        ledger = []

        # Build the entries from the journal
        self.entries = {}
        for row in journal:
            self.entries.setdefault(row["pk"], []).append(row)

        # Build Data for each corporation
        for corporation_id in self.corporations:
            # Create the LedgerEntity object for the entity
            entity_obj = LedgerEntity(
                entity_id=corporation_id,
            )

            # Create Ledger Data for the entity
            corp_data = self.create_entity_data(
                entity=entity_obj,
            )

            if corp_data is None:
                continue

            ledger.append(corp_data)
        return ledger

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
