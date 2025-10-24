# Standard Library
from collections import defaultdict
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

# Django
from django.db.models import QuerySet, TextChoices
from django.db.models.functions import TruncDay, TruncHour, TruncMonth
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@dataclass
class ChartData:
    title: str
    categories: list[str]
    series: list[dict[str, Any]]

    def serialize_decimals(self, obj):
        if isinstance(obj, dict):
            return {k: self.serialize_decimals(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.serialize_decimals(i) for i in obj]
        if isinstance(obj, Decimal):
            return float(obj)
        return obj

    def asdict(self) -> dict:
        """Return this object as dict."""
        serialized_data = self.serialize_decimals(asdict(self))
        return serialized_data


class BillboardSystem:
    """BillboardSystem class to process billboard data."""

    class Categories(TextChoices):
        """Translation Helper"""

        BOUNTY = "Bounty", _("Bounty")
        ESS = "ESS", _("ESS")
        MINING = "Mining", _("Mining")
        MISCELLANEOUS = "Miscellaneous", _("Miscellaneous")
        COSTS = "Costs", _("Costs")
        UNKNOWN = "Unknown", _("Unknown")

    @dataclass
    class BillboardDict:
        """BillboardDict class to store the billboard data."""

        charts: ChartData = None
        rattingbar: ChartData = None

        def asdict(self) -> dict:
            """Return this object as dict."""
            return {
                "charts": self.charts.asdict() if self.charts else None,
                "rattingbar": self.rattingbar.asdict() if self.rattingbar else None,
            }

    def __init__(
        self,
        view: str = "month",
    ):
        self.view = view
        self.dict = self.BillboardDict()
        self.results = defaultdict(lambda: defaultdict(Decimal))

    def _get_formatted_date(self, date, view):
        if view == "year":
            return date.strftime("%Y-%m")
        if view == "month":
            return date.strftime("%Y-%m-%d")
        if self.view == "day":
            return date.strftime("%Y-%m-%d %H:%M")
        raise ValueError("Invalid view type. Use 'day', 'month', or 'year'.")

    def _create_chart_dict(self):
        """Create the Charts dict if it doesn't exist"""
        if self.dict.charts is None:
            self.dict.charts = ChartData(
                title="Billboard",
                categories=[],
                series=[],
            )

    def change_view(self, view: str):
        """Change the view of the billboard"""
        if view not in ["day", "month", "year"]:
            raise ValueError("Invalid view type. Use 'day', 'month', or 'year'.")
        self.view = view

    def chord_add_char_data_from_dict(self, data: dict):
        """Add character data to chord from dict"""
        self._create_chart_dict()

        data_points = [
            {
                "from": f"{data['main_name']}",
                "to": "Wallet",
                "value": abs(data["total_amount"]),
            },
            {
                "from": f"{data['main_name']}",
                "to": "Wallet",
                "value": abs(data["total_amount_ess"]),
            },
            {
                "from": f"{data['main_name']}",
                "to": "Wallet",
                "value": abs(data["total_amount_mining"]),
            },
            {
                "from": f"{data['main_name']}",
                "to": "Wallet",
                "value": abs(data["total_amount_others"]),
            },
            {
                "from": f"{data['main_name']}",
                "to": "Costs",
                "value": abs(data["total_amount_costs"]),
            },
        ]

        for point in data_points:
            if point["value"] != 0:
                self.dict.charts.series.append(point)

    def chord_add_data(self, chord_from: str, chord_to: str, value: int):
        """Add Simple Chord data"""
        self._create_chart_dict()

        if value == 0:
            return

        data = {
            "from": chord_from,
            "to": chord_to,
            "value": value,
        }
        self.dict.charts.series.append(data)

    def chord_handle_overflow(self):
        """Order and handle overflow data for the billboard, for each 'to' category and sort it by from and to."""
        if self.dict.charts is None:
            return

        # Group by 'to' category
        grouped = defaultdict(list)
        for entry in self.dict.charts.series:
            grouped[entry["to"]].append(entry)

        new_series = []
        for to_category, entries in grouped.items():
            # Sort each group by value descending
            sorted_entries = sorted(entries, key=lambda x: x["value"], reverse=True)
            if len(sorted_entries) > 25:
                # Keep top 30, sum the rest as 'Others'
                top_entries = sorted_entries[:25]
                others_value = sum(e["value"] for e in sorted_entries[25:])
                top_entries.append(
                    {
                        "from": "Others",
                        "to": to_category,
                        "value": others_value,
                    }
                )
                new_series.extend(top_entries)
            else:
                new_series.extend(sorted_entries)

        # Sort the final series by value descending for display
        self.dict.charts.series = sorted(
            new_series, key=lambda x: x["value"], reverse=True
        )
        self.sort_chord_data()

    def sort_chord_data(self):
        """Sort the chord data by 'from' and 'to' categories."""
        if self.dict.charts is None:
            return

        self.dict.charts.series.sort(key=lambda x: (x["from"], x["to"]))

    def create_timeline(self, journal: QuerySet):
        """Create the timeline data for the billboard"""
        qs = journal

        if self.view == "year":
            qs = qs.annotate(period=TruncMonth("date"))
        elif self.view == "month":
            qs = qs.annotate(period=TruncDay("date"))
        elif self.view == "day":
            qs = qs.annotate(period=TruncHour("date"))
        else:
            raise ValueError("Invalid view type. Use 'day', 'month', or 'year'.")

        qs = qs.values("period").order_by("period")
        return qs

    def create_or_update_results(
        self,
        qs: QuerySet[dict],
        is_old_ess: bool = False,
    ):
        """Create or update the results for the billboard"""
        for entry in qs:
            date = entry["period"]
            bounty = entry.get("bounty_income", 0)
            ess = entry.get("ess_income", 0)
            miscellaneous = entry.get("miscellaneous", 0)

            self.results[date][self.Categories.BOUNTY] += bounty
            self.results[date][self.Categories.ESS] += (
                ess if not is_old_ess else bounty * Decimal("0.667")
            )
            self.results[date][self.Categories.MISCELLANEOUS] += miscellaneous

        return self.results

    def add_category(self, qs: QuerySet[dict], category: str):
        """Add category data to the results

        **the annotation must be have _income as ending
        """
        for entry in qs:
            date = entry["period"]
            category_value = entry.get(f"{category}_income", 0)
            try:
                self.results[date][self.Categories[category.upper()]] += category_value
            except KeyError:
                self.results[date][self.Categories.UNKNOWN] += category_value

    def generate_xy_series(self):
        """Create the ratting bar amounts and categories for the billboard"""
        series = []
        category_set = set()

        for date, values in self.results.items():
            # Remove categories with value 0
            filtered_values = {str(k): v for k, v in values.items() if v != 0}
            if not filtered_values:
                continue  # Skip if all categories are 0

            series.append(
                {
                    "date": self._get_formatted_date(date, self.view),
                    **{k: int(v) for k, v in filtered_values.items()},
                }
            )
            category_set.update(filtered_values.keys())

        # Create categories
        categories = []
        for cat in sorted(category_set):
            try:
                label = self.Categories(cat).label
            except Exception:  # pylint: disable=broad-except
                label = cat
            categories.append({"name": cat, "label": str(label)})

        if not series:
            return [], []

        # Sort Series by Date
        series.sort(key=lambda x: x["date"])

        return series, categories

    def create_xy_chart(self, title, categories, series):
        """Create the XY chart for the billboard"""
        self.dict.rattingbar = ChartData(
            title=title,
            categories=categories,
            series=series,
        )
