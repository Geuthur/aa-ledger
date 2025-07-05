# Standard Library
from collections import defaultdict
from decimal import Decimal

# Django
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.api.api_helper.aggregator import AggregateLedger
from ledger.api.api_helper.billboard_helper import BillboardSystem
from ledger.api.api_helper.information_helper import (
    InformationData,
)
from ledger.helpers.core import events_filter
from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletJournalEntry,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


# pylint: disable=duplicate-code
class AllianceProcess:
    """JournalProcess class to process the journal entries."""

    def __init__(
        self,
        alliance: EveAllianceInfo,
        date: timezone.datetime,
        corporation: CorporationAudit = None,
        view=None,
    ):
        self.alliance = alliance
        self.corporation = corporation
        self.date = date
        self.view = view
        self.current_date = timezone.now()

        self._init_journal()

    def _filter_date(self):
        """Filter the date."""
        filter_date = Q(date__year=self.date.year)
        if self.view == "month":
            filter_date &= Q(date__month=self.date.month)
        elif self.view == "day":
            filter_date &= Q(date__month=self.date.month)
            filter_date &= Q(date__day=self.date.day)
        return filter_date

    def _init_journal(self):
        """Get the involved characters for the alliance"""
        self.corporation_journal = CorporationWalletJournalEntry.objects.filter(
            self._filter_date(),
            division__corporation__corporation__alliance__alliance_id=self.alliance.alliance_id,
        )

        # Exclude Corp Tax Events
        self.corporation_journal = events_filter(self.corporation_journal)

        # Get Glances
        self.glance = AggregateLedger(self.corporation_journal)

        # Get Entity IDs from Corporation or Alliance
        if self.corporation:
            journal = self.corporation_journal.filter(
                Q(division__corporation=self.corporation)
            )
            self.entity_ids = set(
                journal.values_list("second_party_id", flat=True)
            ) | set(journal.values_list("first_party_id", flat=True))
        else:
            self.entity_ids = set(
                self.corporation_journal.values_list("second_party_id", flat=True)
            ) | set(self.corporation_journal.values_list("first_party_id", flat=True))

        self.glance_day = self.corporation_journal.filter(
            date__year=self.current_date.year,
            date__month=self.current_date.month,
            date__day=self.current_date.day,
        )

    def _process_journal_entry(self, entry, main_dict, billboard):
        """Process a single journal entry."""
        corp_id = entry["division__corporation__corporation__corporation_id"]
        corp_name = entry["division__corporation__corporation__corporation_name"]

        bounty = entry.get("bounty_income", 0)
        ess = entry.get("ess_income", 0)
        miscellaneous = entry.get("miscellaneous", 0)
        costs = entry.get("costs", 0) + self.glance.aggregate_corp_withdraw_cost(
            exclude=corp_id
        )

        if bounty > 0 or ess > 0 or costs > 0 or miscellaneous > 0:
            main_dict[corp_id] = {
                "main_id": corp_id,
                "main_name": corp_name,
                "entity_type": "corporation",
                "total_amount": bounty,
                "total_amount_ess": ess,
                "total_amount_costs": costs,
                "total_amount_others": miscellaneous,
            }

            billboard.chord_add_data(
                corp_name, _("Income"), (bounty + ess + miscellaneous)
            )

    def generate_ledger(self):
        """Generate the ledger for the alliance"""
        main_dict = {}
        billboard = BillboardSystem(view=self.view)
        exclude = self.corporation_journal.values_list(
            "division__corporation__corporation__corporation_id", flat=True
        )

        journal = (
            self.corporation_journal.values(
                "division__corporation__corporation__corporation_id",
                "division__corporation__corporation__corporation_name",
            )
            .annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
            .annotate_costs()
        )

        for entry in journal:
            self._process_journal_entry(entry, main_dict, billboard)

        totals = {
            "total_amount": self.glance.aggregate_bounty(),
            "total_amount_ess": self.glance.aggregate_ess(),
            "total_amount_others": (
                +self.glance.aggregate_miscellaneous()
                + self.glance.aggregate_donation()
                + self.glance.aggregate_corp_withdraw(
                    exclude=exclude
                )  # Exclude Intern Transfers
            ),
            "total_amount_costs": self.glance.aggregate_costs()
            + self.glance.aggregate_corp_withdraw_cost(exclude=exclude),
        }
        totals["total_amount_all"] = (
            totals["total_amount"]
            + totals["total_amount_ess"]
            + totals["total_amount_others"]
            + totals["total_amount_costs"]
        )

        # Add Rattingbar for the corporation
        rattingbar_timeline = billboard.create_timeline(self.corporation_journal)
        rattingbar = (
            rattingbar_timeline.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
        )
        billboard.create_or_update_results(rattingbar)
        billboard.create_ratting_bar()

        # Order and Handle Overflow
        billboard.chord_handle_overflow()

        output = {
            "ratting": sorted(list(main_dict.values()), key=lambda x: x["main_name"]),
            "billboard": billboard.dict,
            "total": totals,
        }

        return output

    def generate_template(self):
        """Generate the information for the corporation"""
        information_dict = {}
        exclude = None

        # Create the Ledger
        ledger_data = InformationData(
            corporation=self.corporation,
            date=self.date,
            view=self.view,
            current_date=self.current_date,
        )

        if self.corporation is not None:
            exclude = self.corporation.corporation.corporation_id
        else:
            exclude = self.corporation_journal.values_list(
                "division__corporation__corporation__corporation_id", flat=True
            )

        day_aggregate = AggregateLedger(self.glance_day)

        amounts = defaultdict(lambda: defaultdict(Decimal))

        amounts["bounty_income"] = {
            "total_amount": self.glance.aggregate_bounty(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_bounty(self.entity_ids),
        }

        amounts["ess_income"] = {
            "total_amount": self.glance.aggregate_ess(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_ess(self.entity_ids),
        }

        amounts["mission_income"] = {
            "total_amount": self.glance.aggregate_mission(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_mission(self.entity_ids),
        }

        amounts["market_income"] = {
            "total_amount": self.glance.aggregate_market(second_party=self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_market(
                second_party=self.entity_ids
            ),
        }

        amounts["contract_income"] = {
            "total_amount": self.glance.aggregate_contract(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_contract(self.entity_ids),
        }

        amounts["donation_income"] = {
            "total_amount": self.glance.aggregate_donation(self.entity_ids)
            + self.glance.aggregate_corp_withdraw(self.entity_ids, exclude=exclude),
            "total_amount_day": day_aggregate.aggregate_donation(self.entity_ids)
            + day_aggregate.aggregate_corp_withdraw(self.entity_ids, exclude=exclude),
        }

        amounts["insurance_income"] = {
            "total_amount": self.glance.aggregate_insurance(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_insurance(self.entity_ids),
        }

        amounts["daily_goal_income"] = {
            "total_amount": self.glance.aggregate_daily_goal(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_daily_goal(self.entity_ids),
        }

        amounts["citadel_income"] = {
            "total_amount": (
                self.glance.aggregate_production(self.entity_ids)
                + self.glance.aggregate_traveling(self.entity_ids)
            ),
            "total_amount_day": (
                day_aggregate.aggregate_production(self.entity_ids)
                + day_aggregate.aggregate_traveling(self.entity_ids)
            ),
        }

        amounts["market_cost"] = {
            "total_amount": self.glance.aggregate_market_cost(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_market_cost(self.entity_ids),
        }

        amounts["rental_cost"] = {
            "total_amount": self.glance.aggregate_rental(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_rental(self.entity_ids),
        }

        amounts["donation_cost"] = {
            "total_amount": self.glance.aggregate_corp_withdraw_cost(
                self.entity_ids, exclude=exclude
            ),
            "total_amount_day": day_aggregate.aggregate_corp_withdraw_cost(
                self.entity_ids, exclude=exclude
            ),
        }

        amounts["contract_cost"] = {
            "total_amount": self.glance.aggregate_contract_cost(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_contract_cost(self.entity_ids),
        }

        amounts["production_cost"] = {
            "total_amount": self.glance.aggregate_production_cost(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_production_cost(
                self.entity_ids
            ),
        }

        information_dict.update(
            {
                "main_id": ledger_data.id,
                "main_name": ledger_data.name,
                "date": ledger_data.information_date,
            }
        )
        information_dict = ledger_data._generate_amounts_dict(amounts, information_dict)
        return information_dict
