"""PvE Views"""

# Standard Library
import json
from decimal import Decimal

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
from ledger.helpers.core import LedgerCore, LedgerEntity
from ledger.helpers.ref_type import RefTypeCategories
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
        self.corporations = CorporationAudit.objects.filter(
            corporation__alliance__alliance_id=self.alliance.alliance_id
        ).values_list("corporation__corporation_id", flat=True)

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
                    row["first_party_id"] in self.entities
                    or row["second_party_id"] in self.entities
                ):
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
            chord_to="Ratting (Wallet)",
            value=bounty,
        )
        self.billboard.chord_add_data(
            chord_from=entity.entity_name,
            chord_to="ESS (Wallet)",
            value=ess,
        )
        self.billboard.chord_add_data(
            chord_from=entity.entity_name,
            chord_to="Costs (Wallet)",
            value=abs(costs),
        )
        self.billboard.chord_add_data(
            chord_from=entity.entity_name,
            chord_to="Miscellaneous (Wallet)",
            value=abs(miscellaneous),
        )

        return entity_ledger_info

    # pylint: disable=duplicate-code
    def generate_ledger_data(self) -> dict:
        """Generate the ledger data for the character and its alts."""
        self.setup_ledger()

        ledger = []
        finished_entities = set()

        journal = self.journal.values(
            "first_party_id", "second_party_id", "pk"
        ).annotate(
            bounty=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeCategories.BOUNTY_PRIZES),
                output_field=DecimalField(),
            ),
            ess=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeCategories.ESS_TRANSFER),
                output_field=DecimalField(),
            ),
            costs=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeCategories.costs(), amount__lt=0),
                output_field=DecimalField(),
            ),
            miscellaneous=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeCategories.miscellaneous(), amount__gt=0),
                output_field=DecimalField(),
            ),
        )

        self.entries = {}
        for row in journal:
            self.entries.setdefault(row["pk"], []).append(row)

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

            char_data = self.create_entity_data(
                entity=entity_obj,
            )

            if char_data is None:
                continue

            ledger.append(char_data)
            finished_entities.add(corporation_id)

        # Create the billboard data
        self.create_rattingbar(list(finished_entities), is_char_ledger=False)
        # Prevent overflow in the chord data
        self.billboard.chord_handle_overflow()

        context = {
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
        return context

    def create_rattingbar(
        self, entities_ids: list = None, is_char_ledger: bool = False
    ):
        """Create the ratting bar for the view."""
        if not entities_ids:
            return

        rattingbar_timeline = self.billboard.create_timeline(self.journal)
        rattingbar = (
            rattingbar_timeline.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
        )
        self.billboard.create_or_update_results(
            rattingbar, is_char_ledger=is_char_ledger
        )
        self.billboard.create_ratting_bar()

    # pylint: disable=duplicate-code
    def _create_corporation_details(self, entity: LedgerEntity) -> dict:
        """Create the corporation amounts for the Details View."""
        self.setup_ledger(entity=entity)

        amounts = {}

        ref_types_income = RefTypeCategories.get_miscellaneous()
        ref_types_costs = RefTypeCategories.get_costs()

        # Bounty Income
        if not entity.entity_id == 1000125:  # Remove Concord Bountys
            bounty_income = self.journal.aggregate_bounty()
            if bounty_income > 0:
                amounts["bounty_income"] = {"total_amount": bounty_income}

        # ESS Income (nur wenn bounty_income existiert)
        ess_income = self.journal.aggregate_ess()
        if ess_income > 0:
            amounts["ess_income"] = {"total_amount": ess_income}

        # Income Ref Types
        for ref_type, value in ref_types_income.items():
            ref_type_name = ref_type.lower()
            aggregated_data = self.journal.aggregate_ref_type(
                ref_type=value,
                income=True,
            )
            if aggregated_data > 0:
                amounts[f"{ref_type_name}_income"] = {"total_amount": aggregated_data}

        # Cost Ref Types
        for ref_type, value in ref_types_costs.items():
            ref_type_name = ref_type.lower()

            aggregated_data = self.journal.aggregate_ref_type(
                ref_type=value,
                income=False,
            )
            if aggregated_data < 0:
                amounts[f"{ref_type_name}_cost"] = {"total_amount": aggregated_data}

        # Summary
        summary = [
            amount
            for amount in amounts.values()
            if isinstance(amount, dict) and "total_amount" in amount
        ]

        summary = sum(
            amount["total_amount"] for amount in summary if "total_amount" in amount
        )

        if summary == 0:
            return None

        amounts["summary"] = {
            "total_amount": summary,
        }

        # Dynamische Income/Cost-Typen für das Template
        income_types = [("bounty_income", _("Ratting")), ("ess_income", _("ESS"))]
        income_types += [
            (f"{ref_type.lower()}_income", _(ref_type.replace("_", " ").title()))
            for ref_type in ref_types_income
        ]
        cost_types = [
            (f"{ref_type.lower()}_cost", _(ref_type.replace("_", " ").title()))
            for ref_type in ref_types_costs
        ]
        amounts["income_types"] = income_types
        amounts["cost_types"] = cost_types
        return amounts
