from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter

from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import (
    CharacterWalletJournalEntry,
)
from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletJournalEntry,
)
from ledger.view_helpers.core import calculate_ess_stolen

logger = get_extension_logger(__name__)


@dataclass
# pylint: disable=too-many-instance-attributes
class InformationData:
    """InformationData class to hold the information data."""

    request: any
    date: timezone.datetime
    view: str
    character: EveCharacter = None
    corporation: CorporationAudit = None
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
        total_sum = sum(
            (
                Decimal(amounts[key]["total_amount"])
                if isinstance(amounts[key]["total_amount"], float)
                else amounts[key]["total_amount"]
            )
            for key in amounts
            if key != "stolen"
        )

        total_current_day_sum = sum(
            (
                Decimal(amounts[key]["total_amount_day"])
                if isinstance(amounts[key]["total_amount_day"], float)
                else amounts[key]["total_amount_day"]
            )
            for key in amounts
            if key != "stolen"
        )

        # Only show daily amount if not year and in the correct month
        if self.view == "month" and self.current_date.month == self.date.month:
            total_current_day_sum = 0

        dict_name.update(
            {
                key: {
                    sub_key: value
                    for sub_key, value in {
                        "total_amount": amounts[key]["total_amount"],
                        "total_amount_day": (
                            amounts[key]["total_amount_day"]
                            if self.view == "month"
                            and self.current_date.month == self.date.month
                            else 0  # Only show daily amount if not year and in the correct month
                        ),
                        "total_amount_hour": (
                            amounts[key]["total_amount_hour"]
                            if key != "mining"
                            # Bad Fix but it works..
                            else amounts[key]["total_amount_day"]
                        ),
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


class InformationProcessCharacter:
    """Create Infomation View for Character Ledger."""

    def __init__(
        self, characters: models.QuerySet[EveCharacter], data: InformationData
    ):
        self.data = data
        self.characters = characters
        self.information_dict = {}

    def _process_character(
        self, character_journal, corporation_journal, mining_journal
    ):
        """Process the corporations."""
        # Process the amounts
        amounts = defaultdict(lambda: defaultdict(Decimal))

        # Get Alts
        linked_character_ids = (
            self.data.character.character_ownership.user.character_ownerships.select_related(
                "character"
            )
            .all()
            .values_list("character__character_id", flat=True)
        )

        # Aggregate Character Amounts for Information Modal
        amounts = character_journal.aggregate_amounts_information_modal(
            amounts=amounts,
            character_ids=self.chars_ids,
            filter_date=self.data.ledger_date,
            exclude=linked_character_ids,
        )

        # Aggregate Mining Amounts for Information Modal
        amounts = mining_journal.aggregate_amounts_information_modal(
            amounts=amounts,
            chars_list=self.chars_ids,
            filter_date=self.data.ledger_date,
        )

        # Aggregate Corporation Amounts for Information Modal
        amounts = corporation_journal.aggregate_amounts_information_modal_character(
            amounts=amounts,
            character_ids=self.chars_ids,
            filter_date=self.data.ledger_date,
        )

        # Calculate the stolen ESS
        amounts["stolen"] = defaultdict(Decimal)
        amounts = calculate_ess_stolen(amounts)

        self.information_dict.update(
            {
                "main_id": self.data.id,
                "main_name": self.data.name,
                "date": self.data.information_date,
            }
        )

        self.information_dict = self.data._generate_amounts_dict(
            amounts, self.information_dict
        )
        return self.information_dict

    def character_information_dict(self):
        """Process the alliance information dict."""
        filter_date = self.data.get_queryfilter_date()

        # Get the character ids
        self.chars_ids = self.characters.values_list("character_id", flat=True)

        character_journal, mining_journal, corporation_journal = (
            CharacterWalletJournalEntry.objects.filter(
                filter_date,
            )
            .select_related("first_party", "second_party")
            .generate_ledger(
                characters=self.characters,
                filter_date=filter_date,
                exclude=self.chars_ids,
            )
        )

        mining_journal = mining_journal.annotate_pricing()

        self.information_dict = self._process_character(
            character_journal, corporation_journal, mining_journal
        )

        return self.information_dict


class InformationProcessCorporation:
    """Create Infomation View for Corporation Ledger."""

    def __init__(self, corporation_id: int, character_ids, data: InformationData):
        self.data = data
        self.corporation_id = corporation_id
        self.character_ids = character_ids
        self.information_dict = {}

    def _process_corporation(self, corporation_journal):
        """Process the corporations."""
        # Process the amounts
        amounts = defaultdict(lambda: defaultdict(Decimal))

        amounts = corporation_journal.aggregate_amounts_information_modal_corporation(
            amounts=amounts,
            filter_date=self.data.ledger_date,
            corporation_id=self.corporation_id,
            character_ids=self.character_ids,
        )

        self.information_dict.update(
            {
                "main_id": self.data.id,
                "main_name": self.data.name,
                "date": self.data.information_date,
            }
        )

        self.information_dict = self.data._generate_amounts_dict(
            amounts, self.information_dict
        )
        return self.information_dict

    def corporation_information_dict(self):
        """Process the alliance information dict."""
        filter_date = self.data.get_queryfilter_date()

        journal = CorporationWalletJournalEntry.objects.filter(
            filter_date
        ).select_related(
            "first_party",
            "second_party",
        )

        self.information_dict = self._process_corporation(journal)
        return self.information_dict


class InformationProcessAlliance:
    """Create Infomation View for Alliance Ledger."""

    def __init__(self, corporations: list, data: InformationData):
        self.data = data
        self.corporations = corporations
        self.information_dict = {}

    def _process_corporation(self, corporation_journal):
        """Process the corporations."""
        # Process the amounts
        amounts = defaultdict(lambda: defaultdict(Decimal))

        amounts = corporation_journal.aggregate_amounts_information_modal_alliance(
            amounts=amounts,
            corporations=self.corporations,
            filter_date=self.data.ledger_date,
        )

        self.information_dict.update(
            {
                "main_id": self.data.id,
                "main_name": self.data.name,
                "date": self.data.information_date,
            }
        )

        self.information_dict = self.data._generate_amounts_dict(
            amounts, self.information_dict
        )
        return self.information_dict

    def alliance_information_dict(self):
        """Process the alliance information dict."""
        filter_date = self.data.get_queryfilter_date()

        journal = CorporationWalletJournalEntry.objects.filter(
            filter_date
        ).select_related(
            "first_party",
            "second_party",
        )

        self.information_dict = self._process_corporation(journal)
        return self.information_dict
