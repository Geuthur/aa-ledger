import logging
from dataclasses import dataclass, field
from typing import Any

from django.db.models import F
from django.db.models.functions import TruncDay, TruncHour, TruncMonth, TruncYear
from django.utils import timezone
from django.utils.translation import gettext as _

from ledger.api.api_helper.core_manager import LedgerModels
from ledger.api.helpers import convert_corp_tax
from ledger.models.corporationaudit import CorporationWalletJournalEntry

logger = logging.getLogger(__name__)


@dataclass
class _BillboardDict:
    charts: Any = field(default_factory=lambda: None)
    rattingbar: Any = field(default_factory=lambda: None)
    workflowgauge: Any = field(default_factory=lambda: None)


@dataclass
class BillboardDict:
    standard: _BillboardDict = field(default_factory=_BillboardDict)


@dataclass
class BillboardTrunc:
    year: tuple = field(default_factory=lambda: (TruncYear("date"), "%Y-%m"))
    month: tuple = field(default_factory=lambda: (TruncMonth("date"), "%Y-%m"))
    week: tuple = field(default_factory=lambda: (TruncDay("date"), "%Y-%m-%d"))
    day: tuple = field(default_factory=lambda: (TruncDay("date"), "%Y-%m-%d"))
    hour: tuple = field(
        default_factory=lambda: (TruncHour("date"), "%Y-%m-%d %H:00:00")
    )


@dataclass
class ChartData:
    title: str
    date: str
    categories: list[str]
    series: list[dict[str, Any]]


@dataclass
class BillboardSystem:
    data_points: dict = field(default_factory=dict)
    chord_data_points: dict = field(default_factory=dict)

    def _clean_category(self, category: str) -> str:
        """Remove the suffix from the category name."""
        return category.split("_")[0].lower()

    def add_or_update_data_point(
        self, date: str, category: str, value: float, data: dict = None
    ):
        mode = "cost" if "cost" in category.lower() else "income"
        display_category = self._clean_category(category)

        # Skip zero values
        if value == 0.0:
            return

        # Create a new data point if it does not exist
        if date not in self.data_points:
            self.data_points[date] = {}
        if display_category not in self.data_points[date]:
            self.data_points[date][display_category] = []

        # Add the new data point
        self.data_points[date][display_category].append(
            {
                "value": value,
                "mode": mode,
                "data": data,
            }
        )

    def add_chord_data_point(self, from_char: str, to: str, value: float):
        if value == 0.0:
            return

        if from_char not in self.chord_data_points:
            self.chord_data_points[from_char] = []

        # Check if from char has already a value for the 'to' value
        for data_point in self.chord_data_points[from_char]:
            if data_point["to"] == to:
                data_point["value"] += value
                break
        else:
            # Add a new data point
            self.chord_data_points[from_char].append(
                {"from": from_char, "to": to, "value": value}
            )

    def to_xy(self, title: str, is_character=False) -> ChartData:
        """Convert the data points to a XY chart."""
        # Define the specific categories we are interested in
        categories = {
            True: (
                ["bounty", "ess", "miscellaneous"],
                ["Bounty", "ESS", "Miscellaneous"],
            ),
            False: (
                ["bounty", "ess", "miscellaneous", "mining"],
                ["Bounty", "ESS", "Miscellaneous", "Mining"],
            ),
        }

        specific_categories, category_names = categories[is_character]

        # Create series data
        series = []
        for date, categories in self.data_points.items():
            data_entry = {"date": date}
            for category in specific_categories:
                total_value = sum(
                    data["value"] for data in categories.get(category, [])
                )
                if total_value != 0.0:
                    data_entry[category] = round(total_value)
            series.append(data_entry)

        # Sort series data by date
        series.sort(key=lambda x: x["date"])

        date = timezone.now().strftime("%Y-%m-%d")
        return ChartData(
            title=title, date=date, categories=category_names, series=series
        )

    def _to_chart(
        self, title: str, included_categories: set, include_mode=False
    ) -> ChartData:
        """Convert the data points to a chart."""
        data_entry = {"date": timezone.now().strftime("%Y-%m-%d")}
        # Initialize dictionaries to hold the aggregated values for cost and income
        aggregated_cost_data = {
            category: {"value": 0.00, "mode": None} for category in included_categories
        }
        aggregated_income_data = {
            category: {"value": 0.00, "mode": None} for category in included_categories
        }

        # Aggregate the values for each category across all dates
        for date, categories in self.data_points.items():
            for category, data_list in categories.items():
                if category in included_categories:
                    for data in data_list:
                        if data["mode"] == "cost":
                            aggregated_cost_data[category]["value"] += abs(
                                data["value"]
                            )
                            aggregated_cost_data[category]["mode"] = data["mode"]
                        elif data["mode"] == "income":
                            aggregated_income_data[category]["value"] += abs(
                                data["value"]
                            )
                            aggregated_income_data[category]["mode"] = data["mode"]

        # Add the aggregated values to the output
        for category, value in aggregated_cost_data.items():
            if value["value"] == 0.0:
                continue
            display_category = f"{category.upper()}" + (
                f" ({value['mode']})" if include_mode else ""
            )
            data_entry[display_category] = {
                "value": float(f"{value['value']:.2f}"),
                "mode": value["mode"],
            }

        for category, value in aggregated_income_data.items():
            if value["value"] == 0.0:
                continue
            display_category = f"{category.upper()}" + (
                f" ({value['mode']})" if include_mode else ""
            )
            data_entry[display_category] = {
                "value": float(f"{value['value']:.2f}"),
                "mode": value["mode"],
            }

        # Create series data with a single entry
        series = [data_entry]
        categories = sorted(list(included_categories))

        date = timezone.now().strftime("%Y-%m-%d")
        return ChartData(title=title, date=date, categories=categories, series=series)

    def _to_chord_chart(self, title: str) -> ChartData:
        """Convert the data points to a bubble chart."""
        series = []
        max_chords = []
        others_summary = {}

        # Fügen Sie die aggregierten Werte zur Ausgabe hinzu
        for main_char, summaries in self.chord_data_points.items():
            if len(max_chords) <= 15:
                max_chords.append(main_char)
            for summary in summaries:
                if main_char in max_chords:
                    series.append(
                        {
                            "from": summary["from"],
                            "to": summary["to"],
                            "value": summary["value"],
                            "main": summary["from"],
                        }
                    )
                else:
                    to = summary["to"]
                    if to not in others_summary:
                        others_summary[to] = 0
                    others_summary[to] += summary["value"]

        # Add summarized "Others" entries to output
        for to_corp, values in others_summary.items():
            series.append(
                {
                    "from": "Others",
                    "to": to_corp,
                    "value": values,
                    "main": "Others",
                }
            )

        date = timezone.now().strftime("%Y-%m-%d")
        return ChartData(
            title=title,
            date=date,
            categories=None,
            series=series,
        )

    def to_xy_data(self, is_character: bool) -> ChartData:
        return self.to_xy(title="Ratting Chart", is_character=is_character)

    def to_chord_data(self) -> ChartData:
        return self._to_chord_chart(title="Chord Chart")

    def to_chart_data(self) -> ChartData:
        excluded_categories = {"costs", "miscellaneous"}
        all_categories = set()

        # Collect all unique categories from the data points
        for categories in self.data_points.values():
            all_categories.update(categories.keys())

        included_categories = all_categories - excluded_categories
        return self._to_chart(
            title="Donut Chart",
            included_categories=included_categories,
            include_mode=True,
        )

    def to_gauge_data(self) -> ChartData:
        included_categories = {"bounty", "ess", "mining", "miscellaneous"}
        return self._to_chart(
            title="Workflow Chart", included_categories=included_categories
        )


class BillboardCharacterLedger:
    def __init__(self, view: str, models: LedgerModels):
        self.view = view
        self.models = models
        self.billboard_dict = BillboardDict()

    def _sort_series(self, chart_data: ChartData) -> ChartData:
        """Sort the series data by category names."""
        for series_item in chart_data.series:
            sorted_series = {
                k: v for k, v in sorted(series_item.items()) if k != "date"
            }
            sorted_series = {"date": series_item["date"], **sorted_series}
            series_item.clear()
            series_item.update(sorted_series)
        return chart_data

    def _process_char_chart(self, billboard: BillboardSystem, corp_qs, period_format):
        """Process Character Chart from Corporation Journal."""
        for entry in corp_qs:
            date = entry["period"].strftime(period_format)
            for key, value in entry.items():
                if key in [
                    "period",
                    "alts",
                    "bounty_income",
                ]:
                    continue
                value = convert_corp_tax(value)
                billboard.add_or_update_data_point(
                    date=date, category=key, value=float(value)
                )

    # pylint: disable=too-many-branches, too-many-locals
    def _process_billboard(
        self, billboard: BillboardSystem, annotations, period_format
    ) -> BillboardSystem:
        """Process the queryset for the billboard."""
        corp_qs = self.models.corp_journal.annotate(**annotations).values("period")

        corp_qs = (
            corp_qs.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
            .annotate_daily_goal_income()
        )

        # Get Character Data
        char_qs = (
            self.models.char_journal.annotate(**annotations)
            .values("period")
            .annotate_billboard(self.chars, self.alts)
        )

        mining_qs = (
            self.models.mining_journal.annotate(**annotations)
            .values("period")
            .annotate_billboard(self.chars)
        )

        # Process Character Journal
        for entry in char_qs:
            date = entry["period"].strftime(period_format)
            for key, value in entry.items():
                if key not in ["period"]:
                    billboard.add_or_update_data_point(
                        date=date, category=key, value=float(value)
                    )
        # Process Mining Journal
        for entry in mining_qs:
            date = entry["period"].strftime(period_format)
            for key, value in entry.items():
                if key not in ["period"]:
                    billboard.add_or_update_data_point(
                        date=date, category="mining", value=float(value)
                    )
        # Process Corp Journal
        self._process_char_chart(billboard, corp_qs, period_format)

        if not billboard.data_points:
            return None

        return billboard

    def annotate_days(self, period, billboard_dict: _BillboardDict, tick=False):
        """Generate the Billboard Data."""
        trunctype, period_format = period
        annotations = {"period": trunctype}
        self.tick = tick

        billboard = BillboardSystem()
        billboard = self._process_billboard(billboard, annotations, period_format)

        if billboard:
            # Create the Chart
            chart = billboard.to_chart_data()
            chart = self._sort_series(chart)
            billboard_dict.charts = chart

            # Create the Ratting Bar
            rattingbar = billboard.to_xy_data(is_character=True)
            billboard_dict.rattingbar = rattingbar

            # Create the Gauge
            gauge = billboard.to_gauge_data()
            billboard_dict.workflowgauge = self._sort_series(gauge)
        return billboard_dict

    # Create the Billboard
    def billboard_ledger(self, chars, alts: list = None):
        """Generate the Billboard Ledger."""
        periods = BillboardTrunc()
        self.chars = chars
        self.alts = alts
        standard = None

        # Create Billboard Month
        if self.view == "year":
            standard = self.annotate_days(periods.month, self.billboard_dict.standard)
        elif self.view == "month":
            standard = self.annotate_days(periods.day, self.billboard_dict.standard)
        elif self.view == "day":
            standard = self.annotate_days(periods.hour, self.billboard_dict.standard)

        # Generate Billboard
        self.billboard_dict.standard = standard

        return self.billboard_dict


class BillboardCorporation:
    def __init__(self, view: str, journal: CorporationWalletJournalEntry):
        self.view = view
        self.journal = journal
        self.billboard_dict = BillboardDict()

    def _sort_series(self, chart_data: ChartData) -> ChartData:
        """Sort the series data by category names."""
        for series_item in chart_data.series:
            sorted_series = {
                k: v for k, v in sorted(series_item.items()) if k != "date"
            }
            sorted_series = {"date": series_item["date"], **sorted_series}
            series_item.clear()
            series_item.update(sorted_series)
        return chart_data

    def _process_corp_chart(self, billboard: BillboardSystem, corp_qs, period_format):
        """Process Corporation Chart from Corporation Journal."""
        for entry in corp_qs:
            date = entry["period"].strftime(period_format)
            main_char_name = entry.get("main_entity_name", "Unknown")
            corporation = entry.get("corporation", "Unknown")
            bounty = entry.get("bounty_income", 0)
            ess = entry.get("ess_income", 0)
            miscellaneous = entry.get("miscellaneous", 0)
            values = bounty + ess + miscellaneous

            for key, value in entry.items():
                if key in [
                    "period",
                    "alts",
                    "main_entity_name",
                    "main_entity_id",
                    "corporation",
                ]:
                    continue
                billboard.add_or_update_data_point(
                    date=date, category=key, value=float(value)
                )

            billboard.add_chord_data_point(
                from_char=main_char_name, to=corporation, value=values
            )

    # pylint: disable=too-many-branches, too-many-locals
    def _process_billboard(
        self, billboard: BillboardSystem, annotations, period_format
    ) -> BillboardSystem:
        """Process the queryset for the billboard."""
        corp_qs = self.journal.annotate(**annotations)

        corp_qs = corp_qs.values(
            "period", "main_entity_id", "main_entity_name"
        ).annotate(
            corporation=F("division__corporation__corporation__corporation_name")
        )

        corp_qs = (
            corp_qs.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
            .annotate_daily_goal_income()
        )

        self._process_corp_chart(billboard, corp_qs, period_format)

        if not billboard.data_points:
            return None

        return billboard

    def annotate_days(self, period, billboard_dict: _BillboardDict, tick=False):
        """Generate the Billboard Data."""
        trunctype, period_format = period
        annotations = {"period": trunctype}
        self.tick = tick

        billboard = BillboardSystem()
        billboard = self._process_billboard(billboard, annotations, period_format)

        if billboard:
            # Create the Chart
            chart = billboard.to_chord_data()
            billboard_dict.charts = chart

            # Create the Ratting Bar
            rattingbar = billboard.to_xy_data(is_character=False)
            billboard_dict.rattingbar = rattingbar

            # Create the Gauge
            gauge = billboard.to_gauge_data()
            billboard_dict.workflowgauge = self._sort_series(gauge)
        return billboard_dict

    # Create the Billboard
    def billboard_ledger(self):
        """Generate the Billboard Ledger."""
        periods = BillboardTrunc()
        standard = None

        # Create Billboard Month
        if self.view == "year":
            standard = self.annotate_days(periods.month, self.billboard_dict.standard)
        elif self.view == "month":
            standard = self.annotate_days(periods.day, self.billboard_dict.standard)
        elif self.view == "day":
            standard = self.annotate_days(periods.hour, self.billboard_dict.standard)

        # Generate Billboard
        self.billboard_dict.standard = standard

        return self.billboard_dict


class BillboardAlliance:
    def __init__(self, view: str, journal: CorporationWalletJournalEntry):
        self.view = view
        self.journal = journal
        self.billboard_dict = BillboardDict()

    def _sort_series(self, chart_data: ChartData) -> ChartData:
        """Sort the series data by category names."""
        for series_item in chart_data.series:
            sorted_series = {
                k: v for k, v in sorted(series_item.items()) if k != "date"
            }
            sorted_series = {"date": series_item["date"], **sorted_series}
            series_item.clear()
            series_item.update(sorted_series)
        return chart_data

    def _process_corp_chart(self, billboard: BillboardSystem, corp_qs, period_format):
        """Process Corporation Chart from Corporation Journal."""
        for entry in corp_qs:
            date = entry["period"].strftime(period_format)
            chord_from = entry.get(
                "division__corporation__corporation__corporation_name", "Unknown"
            )
            chord_to = "Wallet"
            bounty = entry.get("bounty_income", 0)
            ess = entry.get("ess_income", 0)
            miscellaneous = entry.get("miscellaneous", 0)
            values = bounty + ess + miscellaneous

            for key, value in entry.items():
                if key in [
                    "period",
                    "division__corporation__corporation__corporation_name",
                    "division__corporation__corporation__corporation_id",
                    "corporation",
                ]:
                    continue
                billboard.add_or_update_data_point(
                    date=date, category=key, value=float(value)
                )

            billboard.add_chord_data_point(
                from_char=chord_from, to=chord_to, value=values
            )

    # pylint: disable=too-many-branches, too-many-locals
    def _process_billboard(
        self, billboard: BillboardSystem, annotations, period_format
    ) -> BillboardSystem:
        """Process the queryset for the billboard."""
        corp_qs = self.journal.annotate(**annotations)

        corp_qs = corp_qs.values(
            "period",
            "division__corporation__corporation__corporation_id",
            "division__corporation__corporation__corporation_name",
        ).annotate(
            corporation=F("division__corporation__corporation__corporation_name")
        )

        corp_qs = (
            corp_qs.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
            .annotate_daily_goal_income()
        )

        self._process_corp_chart(billboard, corp_qs, period_format)

        if not billboard.data_points:
            return None

        return billboard

    def annotate_days(self, period, billboard_dict: _BillboardDict, tick=False):
        """Generate the Billboard Data."""
        trunctype, period_format = period
        annotations = {"period": trunctype}
        self.tick = tick

        billboard = BillboardSystem()
        billboard = self._process_billboard(billboard, annotations, period_format)

        if billboard:
            # Create the Chart
            chart = billboard.to_chord_data()
            billboard_dict.charts = chart

            # Create the Ratting Bar
            rattingbar = billboard.to_xy_data(is_character=False)
            billboard_dict.rattingbar = rattingbar

            # Create the Gauge
            gauge = billboard.to_gauge_data()
            billboard_dict.workflowgauge = self._sort_series(gauge)
        return billboard_dict

    # Create the Billboard
    def billboard_ledger(self):
        """Generate the Billboard Ledger."""
        periods = BillboardTrunc()
        standard = None

        # Create Billboard Month
        if self.view == "year":
            standard = self.annotate_days(periods.month, self.billboard_dict.standard)
        elif self.view == "month":
            standard = self.annotate_days(periods.day, self.billboard_dict.standard)
        elif self.view == "day":
            standard = self.annotate_days(periods.hour, self.billboard_dict.standard)

        # Generate Billboard
        self.billboard_dict.standard = standard

        return self.billboard_dict
