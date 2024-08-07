import math
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

from django.db.models import DecimalField, Q, Sum
from django.db.models.functions import (
    Coalesce,
    TruncDay,
    TruncHour,
    TruncMonth,
    TruncYear,
)

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
    sum_amount_tick: list = field(default_factory=lambda: ["Tick"])
    total_sum: int = None


@dataclass
class _BillboardDict:
    walletcharts: list = field(default_factory=list)
    charts: list = field(default_factory=list)
    rattingbar: list = field(default_factory=list)
    workflowgauge: list = field(default_factory=list)


@dataclass
class BillboardDict:
    standard: _BillboardDict = field(default_factory=_BillboardDict)
    weekly: _BillboardDict = field(default_factory=_BillboardDict)
    hourly: _BillboardDict = field(default_factory=_BillboardDict)


@dataclass
class BillboardData(LedgerData):
    corporation_dict: dict = field(default_factory=dict)
    total_amount: int = 0


@dataclass
class BillboardBar:
    standard: list = field(default_factory=lambda: ["x"])
    weekly: list = field(default_factory=lambda: ["x"])
    daily: list = field(default_factory=lambda: ["x"])
    hourly: list = field(default_factory=lambda: ["x"])


@dataclass
class BillboardTrunc:
    year: tuple = field(default_factory=lambda: (TruncYear("date"), "%Y-%m"))
    month: tuple = field(default_factory=lambda: (TruncMonth("date"), "%Y-%m"))
    week: tuple = field(default_factory=lambda: (TruncDay("date"), "%Y-%m-%d"))
    day: tuple = field(default_factory=lambda: (TruncDay("date"), "%Y-%m-%d"))
    hour: tuple = field(
        default_factory=lambda: (TruncHour("date"), "%Y-%m-%d %H:00:00")
    )


class BillboardLedger:
    def __init__(
        self, date: LedgerDate, models: LedgerModels, data: BillboardData, corp=False
    ):
        self.is_corp = corp
        self.models = models
        self.date = date
        self.data = data
        self.billboard_dict = BillboardDict()
        self.date_billboard = BillboardBar()

    def annotate_days(self, period, billboard_values, tick=False):
        trunctype, period_format = period
        annotations = {"period": trunctype}
        self.tick = tick

        filters = LedgerFilter(self.chars)

        summary = self.process_billboard(
            annotations, filters, period_format, billboard_values
        )

        return summary

    def process_billboard(self, annotations, filters, period_format, billboard_values):
        self.data_dict = defaultdict(lambda: defaultdict(int))
        summary = BillboardSum()
        if self.models.corp_journal:
            self._process_corp_journal(annotations, filters, period_format)

        if not self.is_corp:
            if self.models.char_journal:
                self._process_char_journal(annotations, filters, period_format)

        for period, data in self.data_dict.items():
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

            summary.sum_amount.append(int(self.data.total_bounty))
            summary.sum_amount_ess.append(int(self.data.total_ess_payout))
            if not self.is_corp:
                summary.sum_amount_misc.append(int(self.data.total_miscellaneous))
                summary.sum_amount_mining.append(int(self.data.total_mining))
            if self.tick:
                summary.sum_amount_tick.append(int(self.data.total_bounty / 3))

            billboard_values.append(period)

        summary.total_sum = self.calculate_total_sum(summary)
        return summary

    def _process_corp_journal(self, annotations, filters, period_format):
        corp_journal = (
            self.models.corp_journal.annotate(**annotations)
            .values("period")
            .annotate(
                total_bounty=Coalesce(
                    Sum(
                        "amount",
                        filter=Q(filters.filter_bounty),
                    ),
                    0,
                    output_field=DecimalField(),
                ),
                total_ess=Coalesce(
                    Sum(
                        "amount",
                        filter=filters.filter_ess,
                    ),
                    0,
                    output_field=DecimalField(),
                ),
            )
            .order_by("period")
        )

        for entry in corp_journal:
            period = entry["period"].strftime(period_format)
            if self.is_corp:
                self.data_dict[period]["total_bounty"] = entry["total_bounty"]
            self.data_dict[period]["total_ess"] = entry["total_ess"]

            if not self.is_corp:
                # Convert the ESS Payout for Character
                self.data_dict[period]["total_ess"] = convert_ess_payout(
                    self.data_dict[period]["total_ess"]
                )

    def _process_char_journal(self, annotations, filters, period_format):
        donations_filter = filters.filter_donation & ~Q(first_party_id__in=self.alts)
        char_journal = (
            self.models.char_journal.annotate(**annotations)
            .values("period")
            .annotate(
                total_bounty=Coalesce(
                    Sum("amount", filter=Q(filters.filter_bounty)),
                    0,
                    output_field=DecimalField(),
                ),
                total_miscellaneous=Coalesce(
                    Sum(
                        "amount",
                        filter=filters.filter_all_misc
                        | filters.filter_all_missions
                        | donations_filter,
                    ),
                    0,
                    output_field=DecimalField(),
                ),
                total_isk=Coalesce(
                    Sum("amount", filter=Q(filters.filter_total)),
                    0,
                    output_field=DecimalField(),
                ),
                total_cost=Coalesce(
                    Sum(
                        "amount",
                        filter=filters.filter_total & ~Q(first_party_id__in=self.chars),
                    ),
                    0,
                    output_field=DecimalField(),
                ),
                total_market_cost=Coalesce(
                    Sum(
                        "amount",
                        filter=filters.filter_market_cost,
                    ),
                    0,
                    output_field=DecimalField(),
                ),
                total_production_cost=Coalesce(
                    Sum(
                        "amount",
                        filter=filters.filter_production_cost,
                    ),
                    0,
                    output_field=DecimalField(),
                ),
            )
            .order_by("period")
        )

        for entry in char_journal:
            period = entry["period"].strftime(period_format)
            self.data_dict[period]["total_bounty"] = entry["total_bounty"]
            self.data_dict[period]["total_miscellaneous"] = entry["total_miscellaneous"]
            self.data_dict[period]["total_isk"] = entry["total_isk"]
            self.data_dict[period]["total_cost"] = entry["total_cost"]
            self.data_dict[period]["total_market_cost"] = entry["total_market_cost"]
            self.data_dict[period]["total_production_cost"] = entry[
                "total_production_cost"
            ]

        if self.models.mining_journal:
            for entry in self.models.mining_journal.values("total", "date"):
                period = entry["date"].strftime(period_format)
                self.data_dict[period]["total_mining"] += (
                    entry["total"] if entry["total"] else 0
                )

    def calculate_total_sum(self, summary: BillboardSum):
        total_sum = sum(
            sum(filter(lambda x: isinstance(x, (int, Decimal)), lst))
            for lst in [
                summary.sum_amount,
                summary.sum_amount_ess,
                summary.sum_amount_misc,
                summary.sum_amount_mining,
            ]
        )
        return total_sum

    def calculate_percentages(self, summary: BillboardSum):
        percentages = [
            (
                (
                    sum(filter(lambda x: isinstance(x, (int, Decimal)), lst))
                    / summary.total_sum
                    * 100
                )
                if summary.total_sum > 0
                else 0
            )
            for lst in [
                summary.sum_amount,
                summary.sum_amount_ess,
                summary.sum_amount_misc,
                summary.sum_amount_mining,
            ]
        ]
        return [math.floor(perc * 10) / 10 for perc in percentages]

    def generate_gauge_data(self, rounded_percentages):
        self.billboard_dict.standard.workflowgauge = (
            [
                ["Ratting", rounded_percentages[0]],
                ["ESS Payout", rounded_percentages[1]],
                ["Miscellaneous", rounded_percentages[2]],
                ["Mining", rounded_percentages[3]],
            ]
            if sum(rounded_percentages)
            else None
        )

    def generate_wallet_ratting_bar(
        self, billboard_dict: _BillboardDict, billboard_values, summary: BillboardSum
    ):
        billboard_dict.rattingbar = (
            (
                [
                    billboard_values,
                    summary.sum_amount,
                    summary.sum_amount_ess,
                    summary.sum_amount_misc,
                    summary.sum_amount_mining,
                    summary.sum_amount_tick,
                ]
            )
            if summary.total_sum
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

        self.billboard_dict.standard.walletcharts = (
            wallet_chart_data
            if any(item[1] != 0 for item in wallet_chart_data)
            else None
        )

    # Generate Charts Billboard for Corporation Ledger
    def generate_wallet_corps_data(self):
        if not self.data.corporation_dict:
            self.billboard_dict.standard.charts = None
            return
        others_percentage = 0
        others_name = "Others"
        chart_entries = []

        sorted_entries = sorted(
            self.data.corporation_dict.values(),
            key=lambda x: x["total_amount"],
            reverse=True,
        )

        for i, entry in enumerate(sorted_entries, start=1):
            percentage = (entry["total_amount"] / self.data.total_amount) * 100
            if i <= 10:
                chart_entries.append([entry["main_name"], percentage])
            else:
                others_percentage += percentage

        if len(self.data.corporation_dict) > 10:
            chart_entries.append([others_name, others_percentage])

        self.billboard_dict.standard.charts = chart_entries

    # Create the Billboard Char Ledger
    def billboard_char_ledger(self, chars, alts: list):
        self.chars = [char.character_id for char in chars]
        self.alts = alts
        periods = BillboardTrunc()

        if self.date.month == 0:
            summary = self.annotate_days(periods.month, self.date_billboard.standard)
        else:
            summary = self.annotate_days(
                periods.hour, self.date_billboard.hourly, tick=True
            )
            self.generate_wallet_ratting_bar(
                self.billboard_dict.hourly, self.date_billboard.hourly, summary
            )

            summary = self.annotate_days(periods.day, self.date_billboard.standard)

        # Create Gauge Billboard
        rounded_percentages = self.calculate_percentages(summary)
        self.generate_gauge_data(rounded_percentages)

        # Create Ratting Bar Billboard
        self.generate_wallet_ratting_bar(
            self.billboard_dict.standard, self.date_billboard.standard, summary
        )

        # Create Wallet Charts Billboard
        self.generate_wallet_charts_data()

        return self.billboard_dict

    # Create the Billboard Corp Ledger
    def billboard_corp_ledger(self, chars: list):
        self.chars = chars
        periods = BillboardTrunc()

        if self.date.month == 0:
            summary = self.annotate_days(periods.month, self.date_billboard.standard)
        else:
            summary = self.annotate_days(periods.day, self.date_billboard.standard)

        self.generate_wallet_ratting_bar(
            self.billboard_dict.standard, self.date_billboard.standard, summary
        )

        self.generate_wallet_corps_data()

        return self.billboard_dict
