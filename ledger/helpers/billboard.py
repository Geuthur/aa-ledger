# Standard Library
from collections import defaultdict
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any

# Django
from django.db.models import QuerySet, TextChoices
from django.db.models.functions import TruncDay, TruncHour, TruncMonth
from django.utils.timezone import datetime
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)

if TYPE_CHECKING:
    # AA Ledger
    from ledger.api.schema import OwnerLedgerRequestInfo


@dataclass
class BillboardData:
    categories: list[dict]
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

    def _get_formatted_date(
        self, date: datetime, request_info: "OwnerLedgerRequestInfo"
    ) -> str:
        """
        Get formatted date string based on the view type.

        Args:
            date (datetime): The date to be formatted.
            request_info (OwnerLedgerRequestInfo): The request information containing view details.

        Returns:
            str: The formatted date string.
        """
        if request_info.day is not None:
            return date.strftime("%Y-%m-%d %H:%M")
        if request_info.month is not None:
            return date.strftime("%Y-%m-%d")
        if request_info.year is not None:
            return date.strftime("%Y-%m")
        raise ValueError("Invalid view type. Use 'day', 'month', or 'year'.")

    # pylint: disable=too-many-branches
    def create_chord_billboard(self, ledger_list) -> BillboardData | None:
        """
        Create chord billboard data from a list of ledger schemas.

        Args:
            ledger_list (list): List of ledger schemas (Character, Entity, Alliance).
        Returns:
            BillboardData | None: The generated chord billboard data or None if no data.
        """
        billboard = BillboardData(
            categories=[],
            series=[],
        )

        if len(ledger_list) == 0:
            return None

        for ledger in ledger_list:
            # Determine ledger type by presence of identifying attributes
            if hasattr(ledger, "character"):
                name = ledger.character.character_name
            elif hasattr(ledger, "entity"):
                name = ledger.entity.entity_name
            elif hasattr(ledger, "corporation"):
                name = ledger.corporation.entity_name
            else:
                name = "Unknown"

            bounty = ledger.ledger.bounty
            ess = ledger.ledger.ess
            miscellaneous = ledger.ledger.miscellaneous
            costs = ledger.ledger.costs

            # Only character ledgers have mining values
            if hasattr(ledger, "character") and hasattr(ledger, "ledger"):
                mining = getattr(ledger.ledger, "mining", 0)
                if mining != 0:
                    data = {
                        "from": name,
                        "to": _("Mining"),
                        "value": abs(mining),
                    }

                    billboard.series.append(data)

            if bounty != 0:
                data = {
                    "from": name,
                    "to": _("Bounty"),
                    "value": abs(bounty),
                }

                billboard.series.append(data)
            if ess != 0:
                data = {
                    "from": name,
                    "to": _("ESS"),
                    "value": abs(ess),
                }

                billboard.series.append(data)
            if miscellaneous != 0:
                data = {
                    "from": name,
                    "to": _("Miscellaneous"),
                    "value": abs(miscellaneous),
                }

                billboard.series.append(data)
            if costs != 0:
                data = {
                    "from": name,
                    "to": _("Costs"),
                    "value": abs(costs),
                }

                billboard.series.append(data)

        # Handle overflow
        if len(billboard.series) > 25:
            self.chord_handle_overflow(billboard)
        return billboard

    def chord_handle_overflow(self, chord_billboard: BillboardData):
        """
        Handle overflow in the chord billboard data by grouping lesser entries into 'Others'.

        Args:
            chord_billboard (BillboardData): The chord billboard data to be processed.

        Returns:
            BillboardData: The updated chord billboard data with overflow handled.
        """
        if chord_billboard is None:
            return chord_billboard

        # Group by 'to' category
        grouped = defaultdict(list)
        for entry in chord_billboard.series:
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
        chord_billboard.series = sorted(
            new_series, key=lambda x: x["value"], reverse=True
        )
        return chord_billboard

    def create_timeline(
        self, journal: QuerySet, request_info: "OwnerLedgerRequestInfo"
    ) -> QuerySet[dict]:
        """

        Create the timeline data for the billboard

        This function annotates the journal entries based on the view type (year, month, day)
        and groups them accordingly.

        Args:
            journal (QuerySet): The journal entries to be processed.

        Returns:
            QuerySet[dict]: Annotated and grouped journal entries.
        """
        qs = journal

        if request_info.day is not None:
            qs = qs.annotate(period=TruncHour("date"))
        elif request_info.month is not None:
            qs = qs.annotate(period=TruncDay("date"))
        elif request_info.year is not None:
            qs = qs.annotate(period=TruncMonth("date"))
        else:
            raise ValueError("Invalid view type. Use 'day', 'month', or 'year'.")

        qs = qs.values("period").order_by("period")
        return qs

    def create_or_update_results(
        self,
        qs: QuerySet[dict],
    ) -> dict[datetime, dict[str, Decimal]]:
        """
        Create or Update the results dictionary from the timeline data
        """
        results = defaultdict(lambda: defaultdict(Decimal))

        for entry in qs:
            date = entry["period"]
            bounty = entry.get("bounty_income", 0)
            ess = entry.get("ess_income", 0)
            miscellaneous = entry.get("miscellaneous", 0)

            results[date][self.Categories.BOUNTY] += bounty
            results[date][self.Categories.ESS] += ess
            results[date][self.Categories.MISCELLANEOUS] += miscellaneous

        return results

    def add_category_to_xy_billboard(
        self,
        results: dict[datetime, dict[str, Decimal]],
        category: str,
        queryset: QuerySet[dict],
    ):
        """
        Add category data to the results dictionary for the XY billboard

        Args:
            results (dict[datetime, dict[str, Decimal]]): The results data to be updated.
            category (str): The category to be added.
            queryset (QuerySet[dict]): The queryset containing the category data.

        Returns:
            dict[datetime, dict[str, Decimal]]: The updated results dictionary.
        """
        for entry in queryset:
            date = entry["period"]
            category_value = entry.get(f"{category}_income", 0)
            try:
                results[date][self.Categories[category.upper()]] += category_value
            except KeyError:
                results[date][self.Categories.UNKNOWN] += category_value
        return results

    def create_xy_billboard(
        self,
        results: dict[datetime, dict[str, Decimal]],
        request_info: "OwnerLedgerRequestInfo",
    ) -> BillboardData | None:
        """
        Create XY Billboard Data

        This function creates the XY billboard data from the results dictionary.

        Args:
            results (dict[datetime, dict[str, Decimal]]): The results data to be processed.
            request_info (OwnerLedgerRequestInfo): The request information containing view details.

        Returns:
            BillboardData | None: The generated XY billboard data or None if no data.
        """
        series = []
        category_set = set()

        for date, values in results.items():
            # Remove categories with value 0
            filtered_values = {str(k): v for k, v in values.items() if v != 0}
            if not filtered_values:
                continue  # Skip if all categories are 0

            series.append(
                {
                    "date": self._get_formatted_date(date, request_info=request_info),
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

        if not series or not categories:
            return None

        # Sort Series by Date
        series.sort(key=lambda x: x["date"])

        return BillboardData(
            categories=categories,
            series=series,
        )
