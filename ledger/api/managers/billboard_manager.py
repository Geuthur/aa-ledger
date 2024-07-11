import math
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

from django.db.models import Case, DecimalField, Q, Sum, When
from django.db.models.functions import Coalesce, TruncDay, TruncMonth

from ledger.api.helpers import convert_ess_payout
from ledger.api.managers.core_manager import (
    LedgerData,
    LedgerDate,
    LedgerFilter,
    LedgerModels,
)
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


@dataclass
class BillboardSum:
    sum_amount: list = field(default_factory=lambda: ["Ratting"])
    sum_amount_ess: list = field(default_factory=lambda: ["ESS Payout"])
    sum_amount_misc: list = field(default_factory=lambda: ["Miscellaneous"])
    sum_amount_mining: list = field(default_factory=lambda: ["Mining"])
    total_sum: int = None


class BillboardLedger:
    def __init__(self, date_data: LedgerDate, models: LedgerModels, corp=False):
        self.is_corp = corp
        self.data = LedgerData()
        self.models = models
        self.date = date_data
        self.sum = BillboardSum()
        self.billboard_dict = {
            "walletcharts": [],
            "charts": [],
            "rattingbar": [],
            "workflowgauge": [],
        }
        self.date_billboard = ["x"]

    def annotate_days(self):
        if self.date.month == 0:
            # Gruppieren nach Monat
            annotations = {"period": TruncMonth("date")}
            period_format = "%Y-%m"
        else:
            # Gruppieren nach Tag
            period_format = "%Y-%m-%d"
            annotations = {"period": TruncDay("date")}

        data_dict = defaultdict(lambda: defaultdict(int))
        filters = LedgerFilter(self.chars)
        donations_filter = filters.filter_donation & ~Q(first_party_id__in=self.chars)

        if self.models.corp_journal:
            corp_journal = (
                self.models.corp_journal.annotate(**annotations)
                .values("period")
                .annotate(
                    total_bounty=Sum(
                        Case(
                            When(filters.filter_bounty, then="amount"),
                            default=0,
                            output_field=DecimalField(),
                        )
                    ),
                    total_ess=Sum(
                        Case(
                            When(filters.filter_ess, then="amount"),
                            default=0,
                            output_field=DecimalField(),
                        )
                    ),
                )
                .order_by("period")
            )

            for entry in corp_journal:
                period = entry["period"].strftime(period_format)
                if self.is_corp:
                    data_dict[period]["total_bounty"] = entry["total_bounty"]
                data_dict[period]["total_ess"] = entry["total_ess"]

                if not self.is_corp:
                    # Convert the ESS Payout for Character
                    data_dict[period]["total_ess"] = convert_ess_payout(
                        data_dict[period]["total_ess"]
                    )

        if self.models.char_journal:
            char_journal = (
                self.models.char_journal.annotate(**annotations)
                .values("period")
                .annotate(
                    total_bounty=Sum(
                        Case(
                            When(filters.filter_bounty, then="amount"),
                            default=0,
                            output_field=DecimalField(),
                        )
                    ),
                    total_miscellaneous=Coalesce(
                        Sum(
                            "amount",
                            filter=filters.filter_market
                            | filters.filter_contract
                            | donations_filter,
                        ),
                        0,
                        output_field=DecimalField(),
                    ),
                    total_isk=Sum(
                        Case(
                            When(filters.filter_total, then="amount"),
                            default=0,
                            output_field=DecimalField(),
                        )
                    ),
                    total_cost=Sum(
                        Case(
                            When(filters.filter_costs, then="amount"),
                            default=0,
                            output_field=DecimalField(),
                        )
                    ),
                    total_market_cost=Sum(
                        Case(
                            When(filters.filter_market_cost, then="amount"),
                            default=0,
                            output_field=DecimalField(),
                        )
                    ),
                    total_production_cost=Sum(
                        Case(
                            When(filters.filter_production, then="amount"),
                            default=0,
                            output_field=DecimalField(),
                        )
                    ),
                )
                .order_by("period")
            )

            for entry in char_journal:
                period = entry["period"].strftime(period_format)
                data_dict[period]["total_bounty"] = entry["total_bounty"]
                data_dict[period]["total_miscellaneous"] = entry["total_miscellaneous"]
                data_dict[period]["total_isk"] = entry["total_isk"]
                data_dict[period]["total_cost"] = entry["total_cost"]
                data_dict[period]["total_market_cost"] = entry["total_market_cost"]
                data_dict[period]["total_production_cost"] = entry[
                    "total_production_cost"
                ]

        if self.models.mining_journal:
            for entry in self.models.mining_journal.values("total", "date"):
                period = entry["date"].strftime(period_format)
                data_dict[period]["total_mining"] += entry["total"]

        for period, data in data_dict.items():
            # Main Data
            self.data.total_bounty = data.get("total_bounty", 0)
            self.data.total_ess_payout = data.get("total_ess", 0)
            self.data.total_miscellaneous = data.get("total_miscellaneous", 0)
            self.data.total_mining = data.get("total_mining", 0)
            # Total
            self.data.total_isk += data.get("total_isk", 0)
            # Costs
            self.data.total_cost += data.get("total_cost", 0)
            self.data.total_market_cost += data.get("total_market_cost", 0)
            self.data.total_production_cost += data.get("total_production_cost", 0)

            self.sum.sum_amount.append(int(self.data.total_bounty))
            self.sum.sum_amount_ess.append(int(self.data.total_ess_payout))
            if not self.is_corp:
                self.sum.sum_amount_misc.append(int(self.data.total_miscellaneous))
                self.sum.sum_amount_mining.append(int(self.data.total_mining))

            logger.debug(
                f"Period: {period}, Total Bounty: {self.data.total_bounty}, Total ESS: {self.data.total_ess_payout}, Total Miscellaneous: {self.data.total_miscellaneous}, Total Mining: {self.data.total_mining}, Total ISK: {self.data.total_isk}, Total Cost: {self.data.total_cost}, Total Market Cost: {self.data.total_market_cost}, Total Production Cost: {self.data.total_production_cost}"
            )

            self.date_billboard.append(period)

    def calculate_total_sum(self):
        self.sum.total_sum = sum(
            sum(filter(lambda x: isinstance(x, (int, Decimal)), lst))
            for lst in [
                self.sum.sum_amount,
                self.sum.sum_amount_ess,
                self.sum.sum_amount_misc,
                self.sum.sum_amount_mining,
            ]
        )

    def calculate_percentages(self):
        percentages = [
            (
                (
                    sum(filter(lambda x: isinstance(x, (int, Decimal)), lst))
                    / self.sum.total_sum
                    * 100
                )
                if self.sum.total_sum > 0
                else 0
            )
            for lst in [
                self.sum.sum_amount,
                self.sum.sum_amount_ess,
                self.sum.sum_amount_misc,
                self.sum.sum_amount_mining,
            ]
        ]
        return [math.floor(perc * 10) / 10 for perc in percentages]

    def generate_gauge_data(self, rounded_percentages):
        self.billboard_dict["workflowgauge"] = (
            [
                ["Ratting", rounded_percentages[0]],
                ["ESS Payout", rounded_percentages[1]],
                ["Miscellaneous", rounded_percentages[2]],
                ["Mining", rounded_percentages[3]],
            ]
            if sum(rounded_percentages)
            else None
        )

    def generate_wallet_ratting_bar(self):
        self.billboard_dict["rattingbar"] = (
            (
                [
                    self.date_billboard,
                    self.sum.sum_amount,
                    self.sum.sum_amount_ess,
                    self.sum.sum_amount_misc,
                    self.sum.sum_amount_mining,
                ]
            )
            if self.sum.total_sum
            else None
        )

    # Generate Charts Billboard for Character Ledger
    def generate_wallet_charts_data(self):
        misc_cost = abs(
            self.data.total_cost
            - self.data.total_production_cost
            - self.data.total_market_cost
        )

        wallet_chart_data = [
            # Earns
            ["Income", int(self.data.total_isk)],
            # Costs
            ["Market Cost", int(abs(self.data.total_market_cost))],
            ["Production Cost", int(abs(self.data.total_production_cost))],
            ["Misc. Cost", int(misc_cost)],
        ]

        self.billboard_dict["walletcharts"] = (
            wallet_chart_data
            if any(item[1] != 0 for item in wallet_chart_data)
            else None
        )

    # Generate Charts Billboard for Corporation Ledger
    def generate_wallet_corps_data(self, corporation_dict, summary_dict_all):
        if not corporation_dict:
            self.billboard_dict["charts"] = None
            return
        others_percentage = 0
        others_name = "Others"
        chart_entries = []

        sorted_entries = sorted(
            corporation_dict.values(), key=lambda x: x["total_amount"], reverse=True
        )

        for i, entry in enumerate(sorted_entries, start=1):
            percentage = (entry["total_amount"] / summary_dict_all) * 100
            if i <= 10:
                chart_entries.append([entry["main_name"], percentage])
            else:
                others_percentage += percentage

        if len(corporation_dict) > 10:
            chart_entries.append([others_name, others_percentage])

        self.billboard_dict["charts"] = chart_entries

    # Create the Billboard Char Ledger
    def billboard_char_ledger(self, chars: list):
        self.chars = chars

        # Greaters the Annotations
        self.annotate_days()

        # Calculate the Total Sums
        self.calculate_total_sum()

        # Create Gauge Billboard
        rounded_percentages = self.calculate_percentages()
        self.generate_gauge_data(rounded_percentages)

        # Create Ratting Bar Billboard
        self.generate_wallet_ratting_bar()

        # Create Wallet Charts Billboard
        self.generate_wallet_charts_data()

        return self.billboard_dict

    # Create the Billboard Corp Ledger
    def billboard_corp_ledger(self, corporation_dict, summary_dict_all, chars_list):
        self.chars = chars_list

        self.annotate_days()

        self.calculate_total_sum()

        self.generate_wallet_ratting_bar()

        self.generate_wallet_corps_data(corporation_dict, summary_dict_all)

        return self.billboard_dict
