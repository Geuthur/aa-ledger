from dataclasses import dataclass, field
from typing import Any

from django.db.models import F
from django.db.models.functions import TruncDay, TruncHour, TruncMonth, TruncYear
from django.utils import timezone

from ledger.api.api_helper.core_manager import LedgerModels
from ledger.api.helpers import convert_corp_tax
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


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
    data_points: dict[str, dict[str, float]] = field(default_factory=dict)

    def _clean_category(self, category: str) -> str:
        if "_" in category:
            parts = category.split("_")
            display_category = parts[0].lower()
        else:
            display_category = category.lower()
        return display_category

    def add_or_update_data_point(
        self, date: str, category: str, value: float, data: dict = None
    ):
        mode = "income" if "income" in category.lower() else "cost"
        display_category = self._clean_category(category)

        # Skip zero values
        if value == 0.0:
            return

        # Create a new data point if it does not exist
        if date not in self.data_points:
            self.data_points[date] = {}
        if display_category not in self.data_points[date]:
            self.data_points[date][display_category] = {
                "value": value,
                "mode": mode,
                "data": data,
            }
        else:
            # Update the existing data point
            self.data_points[date][display_category]["value"] += value

    def to_xy(self, is_character=False) -> ChartData:
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
        series = [
            {
                "date": date,
                **{
                    category: round(categories.get(category, {}).get("value", 0.0))
                    for category in specific_categories
                    if categories.get(category, {}).get("value", 0.0) != 0.0
                },
            }
            for date, categories in self.data_points.items()
        ]

        # Sort series data by date
        series.sort(key=lambda x: x["date"])

        date = timezone.now().strftime("%Y-%m-%d")
        return ChartData(
            title="Billboard Chart", date=date, categories=category_names, series=series
        )

    def _to_percentage(self, included_categories: set) -> ChartData:
        """Convert the data points to a percentage chart."""
        # Initialize a dictionary to hold the aggregated values
        aggregated_data = {
            category: {"value": 0.0, "mode": None} for category in included_categories
        }

        # Aggregate the values for each category across all dates
        for date, categories in self.data_points.items():
            for category, data in categories.items():
                if category in included_categories:
                    aggregated_data[category]["value"] += abs(data["value"])
                    aggregated_data[category]["mode"] = data["mode"]

        # Filter out categories with all zero values
        filtered_aggregated_data = {
            category: value
            for category, value in aggregated_data.items()
            if value["value"] != 0.0
        }

        # Calculate percentages
        total_value = sum(value["value"] for value in filtered_aggregated_data.values())
        data_entry = {"date": timezone.now().strftime("%Y-%m-%d")}
        total_percentage = 0

        # Collect all values in a list
        values_list = list(filtered_aggregated_data.items())

        # Calculate percentages for each category
        for category, value in values_list:
            if total_value != 0:
                percentage = round((value["value"] / total_value) * 100)
            else:
                percentage = 0

            display_category = category.upper()
            data_entry[display_category] = {"value": percentage, "mode": value["mode"]}
            total_percentage += percentage

        # Create series data with a single entry
        series = [data_entry]

        # Ensure categories are in the correct order
        categories = sorted(filtered_aggregated_data.keys())

        date = timezone.now().strftime("%Y-%m-%d")
        return ChartData(
            title="Billboard Chart", date=date, categories=categories, series=series
        )

    def _to_chord_chart(self, included_categories: set) -> ChartData:
        """Convert the data points to a bubble chart."""
        series = []
        max_chords = []

        # Iterate through each date and category to create series entries
        for date, categories in self.data_points.items():
            for category, data in categories.items():
                main_char = data["data"].get("main_id", 0)
                if len(max_chords) <= 15:
                    max_chords.append(main_char)
                if main_char in max_chords:
                    series.append(
                        {
                            "date": date,
                            "from": main_char,
                            "to": data["data"].get("second_party", "Unknown"),
                            "value": abs(data["value"]),
                            "category": category,
                            "mode": data["mode"],
                            "main": main_char,
                        }
                    )

        date = timezone.now().strftime("%Y-%m-%d")
        return ChartData(
            title="Billboard Chart",
            date=date,
            categories=list(included_categories),
            series=series,
        )

    def to_chord_data(self) -> ChartData:
        included_categories = {"bounty", "ess", "mining", "miscellaneous"}
        return self._to_chord_chart(included_categories)

    def to_chart_data(self) -> ChartData:
        excluded_categories = {"costs", "miscellaneous"}
        all_categories = set()

        # Collect all unique categories from the data points
        for categories in self.data_points.values():
            all_categories.update(categories.keys())

        included_categories = all_categories - excluded_categories
        return self._to_percentage(included_categories)

    def to_gauge_data(self) -> ChartData:
        included_categories = {"bounty", "ess", "mining", "miscellaneous"}
        return self._to_percentage(included_categories)


class BillboardLedger:
    def __init__(self, view: str, models: LedgerModels, corp=False):
        self.view = view
        self.models = models
        self.is_corp = corp
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

    # pylint: disable=too-many-branches, too-many-locals
    def _process_billboard(
        self, billboard: BillboardSystem, annotations, period_format
    ):
        """Process the queryset for the billboard."""
        corp_qs = (
            self.models.corp_journal.annotate(**annotations)
            .values("period")
            .annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
            .annotate_daily_goal_income()
        )

        if self.is_corp:
            # TODO make a better way to handle this
            # Generate Chord Data
            corp_chord_qs = (
                self.models.corp_journal.annotate(
                    corporation=F(
                        "division__corporation__corporation__corporation_name"
                    )
                )
                .annotate_bounty_income()
                .annotate_ess_income()
                .annotate_miscellaneous()
            )
            # Max Mains
            max_chords = []
            output = []
            for w in corp_chord_qs:
                main_char = w.get("main_entity_id", 0)
                main_char_name = w.get("main_entity_name", "Unknown")
                if len(max_chords) <= 15:
                    max_chords.append(main_char)
                if main_char in max_chords:
                    bounty = w.get("bounty_income", 0)
                    ess = w.get("ess_income", 0)
                    miscellaneous = w.get("miscellaneous", 0)
                    values = bounty + ess + miscellaneous
                    if values > 0:
                        output.append(
                            {
                                "from": main_char_name,
                                "to": w.get("corporation", "Unknown"),
                                "value": values,
                                "main": main_char_name,
                            }
                        )
                else:
                    bounty = w.get("bounty_income", 0)
                    ess = w.get("ess_income", 0)
                    miscellaneous = w.get("miscellaneous", 0)
                    values = bounty + ess + miscellaneous
                    if values > 0:
                        output.append(
                            {
                                "from": "Others",
                                "to": w.get("corporation", "Unknown"),
                                "value": values,
                                "main": "Others",
                            }
                        )

                self.output = {
                    "title": "Test",
                    "date": timezone.now().strftime("%Y-%m-%d"),
                    "categories": ["bounty", "ess", "mining", "miscellaneous"],
                    "series": output,
                }

        # Get Character Data
        if not self.is_corp:
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
            for entry in char_qs:
                date = entry["period"].strftime(period_format)
                for key, value in entry.items():
                    if key not in ["period"]:
                        billboard.add_or_update_data_point(
                            date=date, category=key, value=float(value)
                        )

            for entry in mining_qs:
                date = entry["period"].strftime(period_format)
                for key, value in entry.items():
                    if key not in ["period"]:
                        billboard.add_or_update_data_point(
                            date=date, category="mining", value=float(value)
                        )
        # Corp Data
        for entry in corp_qs:
            date = entry["period"].strftime(period_format)
            second_party_id = entry.get("main_entity_id", 0)
            first_party_name = "Voices of War"
            main_id = entry.get("main_entity_id", 0)
            data = {
                "first_party": first_party_name,
                "second_party": second_party_id,
                "main_id": main_id,
            }
            for key, value in entry.items():
                if key in ["period", "main_entity_id", "alts"]:
                    continue
                if not self.is_corp and key in ["bounty_income"]:
                    continue
                if not self.is_corp:
                    value = convert_corp_tax(value)
                billboard.add_or_update_data_point(
                    date=date, category=key, value=float(value), data=data
                )

        if not billboard.data_points:
            return None

        return billboard

    def annotate_days(self, period, billboard_dict: _BillboardDict, tick=False):
        trunctype, period_format = period
        annotations = {"period": trunctype}
        self.tick = tick

        billboard = BillboardSystem()
        billboard = self._process_billboard(billboard, annotations, period_format)

        if billboard:
            # Create the Chart
            if self.is_corp:
                # chart = billboard.to_chord_data()
                chart = self.output
            else:
                chart = billboard.to_chart_data()
                chart = self._sort_series(chart)
            billboard_dict.charts = chart

            # Create the Ratting Bar
            rattingbar = billboard.to_xy(self.is_corp)
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
