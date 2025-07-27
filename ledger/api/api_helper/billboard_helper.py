# Standard Library
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

# Django
from django.db.models import QuerySet
from django.db.models.functions import TruncDay, TruncHour, TruncMonth

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

    @dataclass
    class BillboardDict:
        """BillboardDict class to store the billboard data."""

        charts: ChartData = None
        rattingbar: ChartData = None
        workflowgauge: ChartData = None

        def asdict(self) -> dict:
            """Return this object as dict."""
            return {
                "charts": self.charts.asdict() if self.charts else None,
                "rattingbar": self.rattingbar.asdict() if self.rattingbar else None,
                "workflowgauge": (
                    self.workflowgauge.asdict() if self.workflowgauge else None
                ),
            }

    def __init__(
        self,
        view,
    ):
        self.view = view
        self.dict = self.BillboardDict()
        self.results = {}

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
        """Order and handle overflow data for the billboard"""
        if self.dict.charts is None:
            return

        self.dict.charts.series = sorted(
            self.dict.charts.series, key=lambda x: x["value"], reverse=True
        )
        if len(self.dict.charts.series) > 20:
            others_value = sum(entry["value"] for entry in self.dict.charts.series[20:])
            self.dict.charts.series = self.dict.charts.series[:20]
            self.dict.charts.series.append(
                {
                    "from": "Others",
                    "to": "Wallet",
                    "value": others_value,
                }
            )

    # TODO Add Mining to the billboard
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
        self, qs: QuerySet[dict], is_char_ledger: bool = False
    ):
        """Create or update the results for the billboard"""
        for entry in qs:
            date = entry["period"]
            bounty = entry.get("bounty_income", 0)
            ess = entry.get("ess_income", 0)
            miscellaneous = entry.get("miscellaneous", 0)

            # Store the results in a dictionary
            if date not in self.results:
                self.results[date] = {
                    "bounty": 0,
                    "ess": 0,
                    "miscellaneous": 0,
                }
            self.results[date]["bounty"] += bounty
            self.results[date]["ess"] += (
                ess if not is_char_ledger else bounty * Decimal("0.667")
            )
            self.results[date]["miscellaneous"] += miscellaneous

        return self.results

    def create_ratting_bar(self):
        """Create the ratting bar data for the billboard"""
        formatted_results = []

        for date, values in self.results.items():
            # Remove categories with value 0
            filtered_values = {k: v for k, v in values.items() if v != 0}
            if not filtered_values:
                continue  # Skip if all categories are 0

            formatted_results.append(
                {
                    "date": self._get_formatted_date(date, self.view),
                    **{k: int(v) for k, v in filtered_values.items()},
                }
            )

        if not formatted_results:
            return []

        self.dict.rattingbar = ChartData(
            title="Ratting Bar",
            categories=["Bounty", "ESS", "Miscellaneous"],
            series=formatted_results,
        )
        return formatted_results
