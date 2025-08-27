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
from ledger.app_settings import LEDGER_CACHE_STALE
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
        if entity is not None:
            if (
                self.request.GET.get("all", False)
                and entity.entity_id == self.alliance.alliance_id
            ):
                self.journal = CorporationWalletJournalEntry.objects.filter(
                    self.filter_date,
                    division__corporation__corporation__alliance__alliance_id=self.alliance.alliance_id,
                )
            else:
                self.journal = CorporationWalletJournalEntry.objects.filter(
                    self.filter_date,
                    division__corporation__corporation__corporation_id=entity.entity_id,
                )

            self.entities = self.get_all_entities(self.journal)

            self.journal = self.journal.filter(
                Q(first_party_id__in=self.entities)
                | Q(second_party_id__in=self.entities)
            ).exclude(
                Q(ref_type="corporation_account_withdrawal")
                & Q(first_party_id=F("second_party_id"))
            )
        else:
            self.journal = CorporationWalletJournalEntry.objects.filter(
                self.filter_date,
                division__corporation__corporation__alliance__alliance_id=self.alliance.alliance_id,
            ).exclude(
                Q(ref_type="corporation_account_withdrawal")
                & Q(first_party_id=F("second_party_id"))
            )

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

        # Create the chord data for the billboard
        self.billboard.chord_add_data(
            chord_from=entity.entity_name,
            chord_to=_("Bounty (Wallet)"),
            value=bounty,
        )
        self.billboard.chord_add_data(
            chord_from=entity.entity_name,
            chord_to=_("ESS (Wallet)"),
            value=ess,
        )
        self.billboard.chord_add_data(
            chord_from=entity.entity_name,
            chord_to=_("Costs (Wallet)"),
            value=abs(costs),
        )
        self.billboard.chord_add_data(
            chord_from=entity.entity_name,
            chord_to=_("Miscellaneous (Wallet)"),
            value=abs(miscellaneous),
        )

        return entity_ledger_info

    # pylint: disable=duplicate-code
    def generate_ledger_data(self) -> dict:
        """Generate the ledger data for the alliance."""
        ledger = []
        finished_entities = set()

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
            self.alliance.alliance_id, self.year, self.month, self.day
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
        cached_ledger = self._get_cached_ledger(
            journal_up_to_date, ledger_key, ledger_hash
        )
        if cached_ledger is not None:
            return cached_ledger

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
        # Prevent overflow in the chord data
        self.billboard.chord_handle_overflow()

        # Build the context for the ledger view
        context = self._build_context(ledger_hash, ledger)

        cache.set(
            key=ledger_key,
            value=context,
            timeout=LEDGER_CACHE_STALE,
        )
        cache.set(
            key=self._get_ledger_header(
                self.alliance.alliance_id, self.year, self.month, self.day
            ),
            value=ledger_hash,
            timeout=None,  # Cache forever until the journal changes
        )
        return context

    def _build_context(self, journal_hash, ledger):
        """Build the context for the ledger view."""
        return {
            "ledger_hash": journal_hash,
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
