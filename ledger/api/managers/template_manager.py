from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from ledger.api.helpers import convert_ess_payout, get_alts_queryset
from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import (
    CharacterMiningLedger,
    CharacterWalletJournalEntry,
)
from ledger.models.corporationaudit import CorporationWalletJournalEntry
from ledger.view_helpers.core import calculate_ess_stolen, events_filter

logger = get_extension_logger(__name__)


@dataclass
class TemplateData:
    """TemplateData class to store the data."""

    request: any
    main: any
    year: int
    month: int
    current_date: timezone.datetime = None

    def __post_init__(self):
        self.ledger_date = self.current_date
        self.ledger_date = self.ledger_date.replace(year=self.year)
        if self.month != 0:
            self.ledger_date = self.ledger_date.replace(month=self.month)


class TemplateProcess:
    """TemplateProcess class to process the data."""

    def __init__(self, chars: list, data: TemplateData, show_year=False):
        self.data = data
        self.chars = chars
        self.show_year = show_year
        self.template_dict = {}

    # pylint: disable=duplicate-code
    def character_template(self):
        """
        Create the character template.
        return: dict
        """
        # Create Char List
        chars = [char.character_id for char in self.chars]

        filter_date = Q(date__year=self.data.year)
        if not self.data.month == 0:
            filter_date &= Q(date__month=self.data.month)

        # Filter the entries for the current day/month
        character_journal = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=chars) | Q(second_party_id__in=chars), filter_date
        ).select_related("first_party", "second_party")

        corporation_journal = (
            CorporationWalletJournalEntry.objects.filter(
                Q(first_party_id__in=chars) | Q(second_party_id__in=chars), filter_date
            )
            .select_related("first_party", "second_party")
            .order_by("-date")
        )

        # Exclude Events to avoid wrong stats
        corporation_journal = events_filter(corporation_journal)
        mining_journal = (
            CharacterMiningLedger.objects.filter(
                Q(character__character__character_id__in=chars), filter_date
            )
        ).annotate_pricing()

        self._process_characters(character_journal, corporation_journal, mining_journal)
        return self.template_dict

    def corporation_template(self):
        """
        Create the corporation template.
        return: dict
        """

        chars = [char.character_id for char in self.chars]

        filter_date = Q(date__year=self.data.year)
        if not self.data.month == 0:
            filter_date &= Q(date__month=self.data.month)

        corporation_journal = (
            CorporationWalletJournalEntry.objects.filter(
                filter_date, Q(second_party_id__in=chars)
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

        self._update_template_dict(self.data.main)
        self._generate_amounts_dict(amounts)

    # Process the corporation
    def _process_corporation(self, corporation_journal):
        """Process the corporations."""
        # Process the amounts
        amounts = self._process_amounts_corp(self.chars, corporation_journal)
        # Update the template dict
        self._update_template_dict(self.data.main)
        self._generate_amounts_dict(amounts)

    # Update Core Dict
    def _update_template_dict(self, char):
        main_name = char.character_name if not self.show_year else "Summary"
        main_id = char.character_id if not self.show_year else 0
        date = (
            str(self.data.ledger_date.year)
            if self.data.month == 0
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
        current_day = 365 if self.data.month == 0 else self.data.ledger_date.day
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
                        "total_amount": round(amounts[key]["total_amount"], 2),
                        "total_amount_day": (
                            round(amounts[key]["total_amount_day"], 2)
                            if self.data.month != 0
                            and self.data.current_date.month == self.data.month
                            else 0  # Only show daily amount if not year and in the correct month
                        ),
                        "total_amount_hour": (
                            round(amounts[key]["total_amount_hour"], 2)
                            if key != "mining"
                            # Bad Fix but it works..
                            else round(amounts[key]["total_amount_day"], 2)
                        ),
                        "average_day": round(
                            amounts[key]["total_amount"] / current_day, 2
                        ),
                        "average_hour": round(
                            (amounts[key]["total_amount"] / current_day) / 24, 2
                        ),
                        "average_tick": (round((amounts[key]["total_amount"]) / 20, 2)),
                        "current_day_tick": (
                            round(amounts[key]["total_amount_day"] / 20, 2)
                        ),
                        "average_day_tick": (
                            round(amounts[key]["total_amount"] / current_day / 20, 2)
                        ),
                        "average_hour_tick": round(
                            (amounts[key]["total_amount"] / current_day) / 24 / 20, 2
                        ),
                    }.items()
                    if value != 0
                }
                for key in amounts
            }
        )

        self.template_dict["summary"] = {
            "total_amount": round(total_sum, 2),
            "total_amount_day": round(total_sum / current_day, 2),
            "total_amount_hour": round((total_sum / current_day) / 24, 2),
            "total_current_day": (
                round(total_current_day_sum, 2)
                if self.data.month != 0
                and self.data.current_date.month == self.data.month
                else 0
            ),  # Only show daily amount if not year and in the correct month
        }

    # Genereate Amounts for each Char
    def _process_amounts_corp(self, chars, corporation_journal):
        amounts = defaultdict(lambda: defaultdict(Decimal))

        char_ids = [char.character_id for char in chars]

        amounts = corporation_journal.generate_template(
            amounts=amounts,
            character_ids=char_ids,
            filter_date=self.data.ledger_date,
            mode="corporation",
        )

        amounts["stolen"] = defaultdict(Decimal)
        amounts = calculate_ess_stolen(amounts)

        return amounts

    # Generate Amounts for all Chars
    # pylint: disable=too-many-locals
    def _process_amounts_char(self, models, chars_list):
        amounts = defaultdict(lambda: defaultdict(Decimal))

        # Set the models
        character_journal, corporation_journal, mining_journal = models

        # Generate Template for Character Journal
        amounts = character_journal.generate_template(
            amounts, chars_list, self.data.ledger_date, chars_list
        )

        # Generate Template for Mining Journal
        amounts["mining"] = defaultdict(Decimal)
        mining_aggregated = (
            mining_journal.filter(Q(character__character__character_id__in=chars_list))
            .values("total", "date")
            .aggregate(
                total_amount=Coalesce(Sum(F("total")), 0, output_field=DecimalField()),
                total_amount_day=Coalesce(
                    Sum(F("total"), filter=Q(date__day=self.data.current_date.day)),
                    0,
                    output_field=DecimalField(),
                ),
            )
        )
        amounts["mining"]["total_amount"] += mining_aggregated["total_amount"]
        amounts["mining"]["total_amount_day"] += mining_aggregated["total_amount_day"]

        # Generate Template for Corporation Journal
        amounts = corporation_journal.generate_template(
            amounts=amounts, character_ids=chars_list, filter_date=self.data.ledger_date
        )

        # Convert ESS Payout for Character Ledger
        amounts["ess"]["total_amount"] = convert_ess_payout(
            amounts["ess"]["total_amount"]
        )

        amounts["ess"]["total_amount_day"] = convert_ess_payout(
            amounts["ess"]["total_amount_day"]
        )
        # Calculate the stolen ESS
        amounts["stolen"] = defaultdict(Decimal)
        amounts = calculate_ess_stolen(amounts)

        return amounts
