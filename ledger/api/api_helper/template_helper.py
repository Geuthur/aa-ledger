from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as trans

from ledger.api.helpers import get_alts_queryset
from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import CharacterWalletJournalEntry
from ledger.models.corporationaudit import CorporationWalletJournalEntry
from ledger.view_helpers.core import calculate_ess_stolen

logger = get_extension_logger(__name__)


@dataclass
class TemplateData:
    """TemplateData class to store the data."""

    request: any
    main: any
    date: datetime
    view: str
    corporations_ids: list = None
    current_date: timezone.datetime = None

    def __post_init__(self):
        self.ledger_date = self.current_date
        self.ledger_date = self.ledger_date.replace(year=self.date.year)
        if self.view == "month":
            self.ledger_date = self.ledger_date.replace(month=self.date.month)
        elif self.view == "day":
            self.ledger_date = self.ledger_date.replace(
                month=self.date.month, day=self.date.day
            )


class TemplateProcess:
    """TemplateProcess class to process the data."""

    def __init__(self, chars: list, data: TemplateData, show_year=False):
        self.data = data
        self.chars = chars
        self.show_year = show_year
        self.template_dict = {}

    def filter_date(self):
        """Filter the date."""
        filter_date = Q(date__year=self.data.date.year)
        if self.data.view == "month":
            filter_date &= Q(date__month=self.data.date.month)
        elif self.data.view == "day":
            filter_date &= Q(date__month=self.data.date.month)
            filter_date &= Q(date__day=self.data.date.day)
        return filter_date

    # pylint: disable=duplicate-code
    def character_template(self):
        """
        Create the character template.
        return: dict
        """
        # Create Char List
        chars = self.chars
        chars_ids = [char.character_id for char in self.chars]

        filter_date = self.filter_date()

        character_journal, mining_journal, corporation_journal = (
            CharacterWalletJournalEntry.objects.filter(
                filter_date,
            )
            .select_related("first_party", "second_party")
            .generate_ledger(
                characters=chars,
                filter_date=filter_date,
                exclude=chars_ids,
            )
        )
        mining_journal = mining_journal.annotate_pricing()

        self._process_characters(character_journal, corporation_journal, mining_journal)
        return self.template_dict

    def corporation_template(self):
        """
        Create the corporation template.
        return: dict
        """

        filter_date = self.filter_date()

        corporation_journal = (
            CorporationWalletJournalEntry.objects.filter(
                filter_date,
            )
            .select_related("first_party", "second_party")
            .order_by("-date")
        )

        self._process_corporation(corporation_journal)
        return self.template_dict

    # Process the character
    def _process_characters(
        self, character_journal, corporation_journal, mining_journal
    ):
        """Process the characters."""
        # Get the alts of the main character
        alts = get_alts_queryset(self.data.main)
        chars_list = [char.character_id for char in alts]

        # Get journals
        models = character_journal, corporation_journal, mining_journal
        # Process the amounts
        amounts = self._process_amounts_char(models, chars_list)

        main_name = (
            self.data.main.character_name if not self.show_year else trans("Summary")
        )
        main_id = self.data.main.character_id if not self.show_year else 0

        self._update_template_dict(main_id, main_name)
        self._generate_amounts_dict(amounts)

    # Process the corporation
    def _process_corporation(self, corporation_journal):
        """Process the corporations."""
        chars = [char.eve_id for char in self.chars]
        # Process the amounts
        amounts = defaultdict(lambda: defaultdict(Decimal))

        amounts = corporation_journal.generate_template(
            amounts=amounts,
            character_ids=chars,
            corporations_ids=self.data.corporations_ids,
            filter_date=self.data.ledger_date,
            entity_type="corporation",
        )

        amounts["stolen"] = defaultdict(Decimal)
        amounts = calculate_ess_stolen(amounts)

        main_name = (
            self.data.main.character_name if not self.show_year else trans("Summary")
        )
        main_id = self.data.main.character_id if not self.show_year else 0

        # Update the template dict
        self._update_template_dict(main_id, main_name)
        self._generate_amounts_dict(amounts)

    # Update Core Dict
    def _update_template_dict(self, main_id=0, main_name=trans("Unknown")):
        date = (
            str(self.data.ledger_date.year)
            if self.data.view == "year"
            else self.data.ledger_date.strftime("%B")
        )
        self.template_dict.update(
            {
                "main_name": main_name,
                "main_id": main_id,
                "date": date,
            }
        )

    # Add Amounts to Dict
    def _generate_amounts_dict(self, amounts):
        """Generate the amounts dictionary."""
        current_day = 365 if self.data.view == "year" else self.data.ledger_date.day
        # Calculate the total sum
        total_sum = sum(
            amounts[key]["total_amount"] for key in amounts if key != "stolen"
        )

        total_current_day_sum = sum(
            amounts[key]["total_amount_day"] for key in amounts if key != "stolen"
        )

        self.template_dict.update(
            {
                key: {
                    sub_key: value
                    for sub_key, value in {
                        "total_amount": amounts[key]["total_amount"],
                        "total_amount_day": (
                            amounts[key]["total_amount_day"]
                            if self.data.view == "month"
                            and self.data.current_date.month == self.data.date.month
                            else 0  # Only show daily amount if not year and in the correct month
                        ),
                        "total_amount_hour": (
                            amounts[key]["total_amount_hour"]
                            if key != "mining"
                            # Bad Fix but it works..
                            else amounts[key]["total_amount_day"]
                        ),
                        "average_day": amounts[key]["total_amount"] / current_day,
                        "average_hour": (amounts[key]["total_amount"] / current_day)
                        / 24,
                        "average_tick": ((amounts[key]["total_amount"]) / 20),
                        "current_day_tick": (amounts[key]["total_amount_day"] / 20),
                        "average_day_tick": (
                            amounts[key]["total_amount"] / current_day / 20
                        ),
                        "average_hour_tick": (
                            amounts[key]["total_amount"] / current_day
                        )
                        / 24
                        / 20,
                    }.items()
                    if value != 0
                }
                for key in amounts
            }
        )

        self.template_dict["summary"] = {
            "total_amount": total_sum,
            "total_amount_day": total_sum / current_day,
            "total_amount_hour": (total_sum / current_day) / 24,
            "total_current_day": (
                total_current_day_sum
                if self.data.view == "month"
                and self.data.current_date.month == self.data.date.month
                else 0
            ),  # Only show daily amount if not year and in the correct month
        }

    # Generate Amounts for all Chars
    # pylint: disable=too-many-locals
    def _process_amounts_char(self, models, chars_list):
        amounts = defaultdict(lambda: defaultdict(Decimal))

        # Set the models
        character_journal, corporation_journal, mining_journal = models

        # Generate Template for Character Journal
        amounts = character_journal.generate_template(
            amounts=amounts,
            character_ids=chars_list,
            filter_date=self.data.ledger_date,
            exclude=chars_list,
        )

        # Generate Template for Mining Journal
        amounts = mining_journal.generate_template(
            amounts=amounts,
            chars_list=chars_list,
            filter_date=self.data.ledger_date,
        )

        # Generate Template for Corporation Journal
        amounts = corporation_journal.generate_template(
            amounts=amounts,
            character_ids=chars_list,
            corporations_ids=self.data.corporations_ids,
            filter_date=self.data.ledger_date,
        )

        # Calculate the stolen ESS
        amounts["stolen"] = defaultdict(Decimal)
        amounts = calculate_ess_stolen(amounts)
        return amounts
