"""PvE Views"""

# Standard Library
import json
from decimal import Decimal

# Django
from django.core.cache import cache
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
from ledger.app_settings import LEDGER_CACHE_ENABLED, LEDGER_CACHE_STALE
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
        request: WSGIRequest,
        alliance: EveAllianceInfo,
        year=None,
        month=None,
        day=None,
    ):
        LedgerCore.__init__(self, year, month, day)
        self.request = request
        self.alliance = alliance
        self.corporations = CorporationAudit.objects.filter(
            corporation__alliance__alliance_id=self.alliance.alliance_id
        ).values_list("corporation__corporation_id", flat=True)
        # Evaluate the existing years for the view
        self.existing_years = (
            CorporationWalletJournalEntry.objects.filter(
                division__corporation__corporation__alliance__alliance_id=self.alliance.alliance_id
            )
            .exclude(date__year__isnull=True)
            .values_list("date__year", flat=True)
            .order_by("-date__year")
            .distinct()
        )
        self.auth_char_ids = self.auth_character_ids

    def setup_ledger(self, entity: LedgerEntity = None):
        """Setup the Ledger Data for the Corporation."""
        alliance_id = self.alliance.alliance_id

        # Base queryset filtered by date and alliance
        base_qs = CorporationWalletJournalEntry.objects.filter(
            self.filter_date,
            division__corporation__corporation__alliance__alliance_id=alliance_id,
        )

        # No entity specified: show all entries for the alliance (preserve existing exclusion)
        if entity is None:
            self.journal = base_qs.exclude(
                Q(ref_type="corporation_account_withdrawal")
                & Q(first_party_id=F("second_party_id"))
            )
            # Prepare auxiliary data used by the view
            self.entities = self.get_all_entities(self.journal)
            return

        # If the entity is the alliance itself and "all" is set, show all alliance entries
        if self.request.GET.get("all", False) and entity.entity_id == alliance_id:
            self.journal = base_qs.exclude(
                Q(ref_type="corporation_account_withdrawal")
                & Q(first_party_id=F("second_party_id"))
            )
            self.entities = self.get_all_entities(self.journal)
            return

        # Regular entity filtering: include any rows where the entity is a first or second party
        entity_ids = entity.get_alts_ids_or_self()
        qs = base_qs.filter(
            Q(first_party_id__in=entity_ids) | Q(second_party_id__in=entity_ids)
        )
        qs = qs.exclude(
            Q(ref_type="corporation_account_withdrawal")
            & Q(first_party_id=F("second_party_id"))
        )

        # If entity represents a corporation or alliance, exclude auth account character IDs
        # that are not part of the current entity to avoid double counting
        if entity.type in ["alliance", "corporation"]:
            exclude_ids = self.auth_char_ids - set(entity_ids)
            qs = qs.exclude(
                Q(first_party_id__in=exclude_ids) | Q(second_party_id__in=exclude_ids)
            )

        self.journal = qs
        self.entities = self.get_all_entities(self.journal)

    def get_all_entities(
        self, journal: QuerySet[CorporationWalletJournalEntry]
    ) -> list[int]:
        """Get all entities in the alliance."""
        entities_ids = set(journal.values_list("second_party_id", flat=True)) | set(
            journal.values_list("first_party_id", flat=True)
        )
        return list(entities_ids)

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
        ledger = False
        finished_entities = False

        self.setup_ledger()

        journal = self.journal.values(
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

        # Build up the journal Cache
        ledger_hash = self._get_ledger_journal_hash(self.journal.values_list("pk"))
        ledger_header = self._get_ledger_header(
            ledger_args=f"{self.alliance.alliance_id}",
            year=self.year,
            month=self.month,
            day=self.day,
        )
        cache_header = cache.get(
            ledger_header,
        )
        logger.debug(
            f"Ledger Header: {ledger_header}, Cache Header: {cache_header}, Journal Hash: {ledger_hash}"
        )

        # Check if the journal is up to date
        journal_up_to_date = cache_header == ledger_hash
        ledger_key = self._build_ledger_cache_key(ledger_header)

        # Check if we have newest cached version of the ledger
        if journal_up_to_date and LEDGER_CACHE_ENABLED:
            ledger = cache.get(f"{ledger_key}-data", False)
            finished_entities = cache.get(f"{ledger_key}-finished_entities", False)

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
                    viewname="alliance_details",
                    alliance_id=self.alliance.alliance_id,
                    entity_id=corporation_id,
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

        # Create the billboard data
        self.create_rattingbar(list(finished_entities))
        self.create_chord(ledger)

        # Build the context for the ledger view
        context = self._build_context(ledger=ledger)

        cache.set(key=f"{ledger_key}-data", value=ledger, timeout=LEDGER_CACHE_STALE)
        cache.set(
            key=f"{ledger_key}-finished_entities",
            value=finished_entities,
            timeout=LEDGER_CACHE_STALE,
        )
        cache.set(
            key=self._get_ledger_header(
                ledger_args=f"{self.alliance.alliance_id}",
                year=self.year,
                month=self.month,
                day=self.day,
            ),
            value=ledger_hash,
            timeout=None,  # Cache forever until the journal changes
        )
        return context

    def _build_context(self, ledger):
        """Build the context for the ledger view."""
        return {
            "title": f"Alliance Ledger - {self.alliance.alliance_name}",
            "alliance_id": self.alliance.alliance_id,
            "billboard": json.dumps(self.billboard.dict.asdict()),
            "ledger": ledger,
            "years": list(self.existing_years),
            "totals": self._calculate_totals(ledger),
            "view": self.create_view_data(
                viewname="alliance_details",
                alliance_id=self.alliance.alliance_id,
                entity_id=self.alliance.alliance_id,
            ),
        }

    def create_rattingbar(self, entities_ids: list = None):
        """Create the ratting bar for the view."""
        if not entities_ids:
            return

        rattingbar_timeline = self.billboard.create_timeline(self.journal)
        rattingbar = (
            rattingbar_timeline.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
        )
        self.billboard.create_or_update_results(rattingbar)
        self._build_xy_chart(title=_("Ratting Bar"))

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
