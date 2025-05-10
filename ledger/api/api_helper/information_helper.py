# Standard Library
from collections import defaultdict
from dataclasses import dataclass

# Django
from django.db.models import Q
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo, EveCharacter
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.models.corporationaudit import (
    CorporationAudit,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@dataclass
# pylint: disable=too-many-instance-attributes
class InformationData:
    """InformationData class to hold the information data."""

    date: timezone.datetime
    view: str
    character: EveCharacter = None
    corporation: CorporationAudit = None
    alliance: EveAllianceInfo = None
    current_date: timezone.datetime = None

    def __post_init__(self):
        self.ledger_date = self.current_date
        self.ledger_date = self.ledger_date.replace(year=self.date.year)
        if self.view == "month":
            self.ledger_date = self.ledger_date.replace(month=self.date.month)
            self.information_date = self.ledger_date.strftime("%B %Y")
        elif self.view == "day":
            self.ledger_date = self.ledger_date.replace(
                month=self.date.month, day=self.date.day
            )
            self.information_date = self.ledger_date.strftime("%d %B %Y")

        if self.view == "year":
            self.current_day = 365
            self.information_date = self.ledger_date.year
        else:
            self.current_day = self.ledger_date.day

        # Information Title
        if self.character is not None:
            self.name = self.character.character_name
            self.id = self.character.character_id
        elif self.corporation is not None:
            self.name = self.corporation.corporation.corporation_name
            self.id = self.corporation.corporation.corporation_id
        elif self.alliance is not None:
            self.name = self.alliance.alliance_name
            self.id = self.alliance.alliance_id
        else:
            self.name = "Unknown"
            self.id = 0

    def get_queryfilter_date(self):
        """Get a query filter date."""
        filter_date = Q(date__year=self.date.year)
        if self.view == "month":
            filter_date &= Q(date__month=self.date.month)
        elif self.view == "day":
            filter_date &= Q(date__month=self.date.month)
            filter_date &= Q(date__day=self.date.day)
        return filter_date

    def _generate_amounts_dict(self, amounts: defaultdict, dict_name: dict):
        """Generate the amounts dictionary."""
        # Convert float values to Decimal before summing
        total_sum = sum(amounts[key]["total_amount"] for key in amounts)

        total_current_day_sum = sum(amounts[key]["total_amount_day"] for key in amounts)

        dict_name.update(
            {
                key: {
                    sub_key: value
                    for sub_key, value in {
                        "total_amount": amounts[key]["total_amount"],
                        "total_amount_day": amounts[key]["total_amount_day"],
                        "average_day": amounts[key]["total_amount"] / self.current_day,
                        "average_hour": (
                            amounts[key]["total_amount"] / self.current_day
                        )
                        / 24,
                        "average_tick": ((amounts[key]["total_amount"]) / 20),
                        "current_day_tick": (amounts[key]["total_amount_day"] / 20),
                        "average_day_tick": (
                            amounts[key]["total_amount"] / self.current_day / 20
                        ),
                        "average_hour_tick": (
                            amounts[key]["total_amount"] / self.current_day
                        )
                        / 24
                        / 20,
                    }.items()
                    if value != 0
                }
                for key in amounts
            }
        )

        dict_name["summary"] = {
            "total_amount": total_sum,
            "total_amount_day": total_sum / self.current_day,
            "total_amount_hour": (total_sum / self.current_day) / 24,
            "total_current_day": total_current_day_sum,
        }
        return dict_name
