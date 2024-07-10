from dataclasses import dataclass
from datetime import datetime

from django.db.models import DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce

from ledger.api.helpers import (
    convert_ess_payout,
    get_alts_queryset,
    get_character,
    get_models_and_string,
)
from ledger.api.managers.core_manager import LedgerFilter
from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import CorporationWalletJournalEntry
from ledger.view_helpers.core import events_filter

CharacterMiningLedger, CharacterWalletJournalEntry = get_models_and_string()

logger = get_extension_logger(__name__)


@dataclass
class TemplateData:
    """TemplateData class to store the data."""

    request: any
    request_id: int
    year: int
    month: int
    ledger_date: datetime = datetime.now()
    current_date: datetime = datetime.now()

    def __post_init__(self):
        self.ledger_date = self.ledger_date.replace(year=self.year)
        if self.month != 0:
            self.ledger_date = self.ledger_date.replace(month=self.month)


@dataclass
class TemplateTotalCore:
    """TemplateTotalCore class to store the core data."""

    bounty: int = 0
    ess: int = 0
    mining: int = 0
    contract: int = 0
    transaction: int = 0
    donation: int = 0
    production_cost: int = 0
    market_cost: int = 0


@dataclass
class TemplateTotalDay:
    """TemplateTotalDay class to store the daily data."""

    bounty_day: int = 0
    ess_day: int = 0
    mining_day: int = 0
    contract_day: int = 0
    transaction_day: int = 0
    donation_day: int = 0
    production_cost_day: int = 0
    market_cost_day: int = 0


@dataclass
class TemplateTotalHour:
    """TemplateTotalHour class to store the hourly data."""

    bounty_hour: int = 0
    ess_hour: int = 0
    mining_hour: int = 0
    contract_hour: int = 0
    transaction_hour: int = 0
    donation_hour: int = 0
    production_cost_hour: int = 0
    market_cost_hour: int = 0


@dataclass
class TemplateTotal(TemplateTotalCore, TemplateTotalDay, TemplateTotalHour):
    """TemplateTotal class to store the data."""

    def to_dict(self):
        return {
            "bounty": {
                "total_amount": self.bounty,
                "total_amount_day": self.bounty_day,
                "total_amount_hour": self.bounty_hour,
            },
            "ess": {
                "total_amount": self.ess,
                "total_amount_day": self.ess_day,
                "total_amount_hour": self.ess_hour,
            },
            "mining": {
                "total_amount": self.mining,
                "total_amount_day": self.mining_day,
            },
            "contract": {
                "total_amount": self.contract,
                "total_amount_day": self.contract_day,
                "total_amount_hour": self.contract_hour,
            },
            "transaction": {
                "total_amount": self.transaction,
                "total_amount_day": self.transaction_day,
                "total_amount_hour": self.transaction_hour,
            },
            "donation": {
                "total_amount": self.donation,
                "total_amount_day": self.donation_day,
                "total_amount_hour": self.donation_hour,
            },
            "production_cost": {
                "total_amount": self.production_cost,
                "total_amount_day": self.production_cost_day,
                "total_amount_hour": self.production_cost_hour,
            },
            "market_cost": {
                "total_amount": self.market_cost,
                "total_amount_day": self.market_cost_day,
                "total_amount_hour": self.market_cost_hour,
            },
        }


class TemplateProcess:
    """TemplateProcess class to process the data."""

    def __init__(self, chars, data: TemplateData, show_year=False):
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

        filters = LedgerFilter(chars)

        filter_date = Q(date__year=self.data.year)
        if not self.data.month == 0:
            filter_date &= Q(date__month=self.data.month)

        # Filter the entries for the current day/month
        character_journal = CharacterWalletJournalEntry.objects.filter(
            filters.filter_partys, filter_date
        ).select_related("first_party", "second_party")

        corporation_journal = (
            CorporationWalletJournalEntry.objects.filter(
                filters.filter_partys, filter_date
            )
            .select_related("first_party", "second_party")
            .order_by("-date")
        )

        # Exclude Events to avoid wrong stats
        corporation_journal = events_filter(corporation_journal)
        mining_journal = (
            CharacterMiningLedger.objects.filter(filters.filter_mining, filter_date)
        ).annotate_pricing()

        self._process_characters(character_journal, corporation_journal, mining_journal)
        return self.template_dict

    def corporation_template(self):
        """
        Create the corporation template.
        return: dict
        """

        chars = [char.character_id for char in self.chars]

        filters = LedgerFilter(chars)
        filter_date = Q(date__year=self.data.year)
        if not self.data.month == 0:
            filter_date &= Q(date__month=self.data.month)

        corporation_journal = (
            CorporationWalletJournalEntry.objects.filter(
                filters.filter_second_party, filter_date
            )
            .select_related("first_party", "second_party", "division")
            .values("amount", "date", "second_party_id", "ref_type")
            .order_by("-date")
        )

        self._process_corporation(corporation_journal)
        return self.template_dict

    # Process the character
    def _process_characters(
        self, character_journal, corporation_journal, mining_journal
    ):
        """Process the characters."""
        _, main = get_character(self.data.request, self.data.request_id)

        alts = get_alts_queryset(main)

        chars_list = [char.character_id for char in alts]

        total_amounts = TemplateTotal().to_dict()

        models = character_journal, corporation_journal, mining_journal

        for char in self.chars:
            amounts = self._process_amounts_char(char, models, chars_list)

            # Add amounts to total_amounts
            for key, value in amounts.items():
                for sub_key, sub_value in value.items():
                    total_amounts[key][sub_key] += sub_value

            self._update_template_dict(char)
        self._generate_amounts_dict(total_amounts)

    # Process the corporation
    def _process_corporation(self, corporation_journal):
        """Process the corporations."""
        total_amounts = TemplateTotal().to_dict()

        for char in self.chars:
            amounts = self._process_amounts_corp(char, corporation_journal)
            # Add amounts to total_amounts
            for key, value in amounts.items():
                for sub_key, sub_value in value.items():
                    total_amounts[key][sub_key] += sub_value

            self._update_template_dict(char)

        self._generate_amounts_dict(total_amounts)

    # Aggregate Journal
    def _aggregate_journal(self, journal):
        result = journal.aggregate(
            total_amount=Coalesce(Sum(F("amount")), 0, output_field=DecimalField()),
            total_amount_day=Coalesce(
                Sum(
                    F("amount"),
                    filter=Q(
                        date__year=self.data.current_date.year,
                        date__month=self.data.current_date.month,
                        date__day=self.data.current_date.day,
                    ),
                ),
                0,
                output_field=DecimalField(),
            ),
            total_amount_hour=Coalesce(
                Sum(
                    F("amount"),
                    filter=Q(
                        date__year=self.data.current_date.year,
                        date__month=self.data.current_date.month,
                        date__day=self.data.current_date.day,
                        date__hour=self.data.current_date.hour,
                    ),
                ),
                0,
                output_field=DecimalField(),
            ),
        )
        if self.data.month == 0:
            result["total_amount_day"] = 0
        return result

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
        total_sum = sum(amounts[key]["total_amount"] for key in amounts)

        self.template_dict.update(
            {
                key: {
                    sub_key: value
                    for sub_key, value in {
                        "total_amount": round(amounts[key]["total_amount"], 2),
                        "total_amount_day": (
                            round(amounts[key]["total_amount_day"], 2)
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
        }

    # Genereate Amounts for each Char
    def _process_amounts_corp(self, char, corporation_journal):
        char_id = char.character_id

        # Create the filters
        filters = LedgerFilter([char_id])

        # Calculate the amounts
        amounts = {
            # Calculate Income
            "bounty": self._aggregate_journal(
                corporation_journal.filter(filters.filter_bounty)
            ),
            "ess": self._aggregate_journal(
                corporation_journal.filter(filters.filter_ess)
            ),
        }
        return amounts

    # Genereate Amounts for each Char
    def _process_amounts_char(self, char, models, chars_list):
        char_id = char.character_id

        # Create the filters
        filters = LedgerFilter([char_id])

        # Set the models
        character_journal, corporation_journal, mining_journal = models

        # Calculate the amounts
        amounts = {
            # Calculate Income
            "bounty": self._aggregate_journal(
                character_journal.filter(filters.filter_bounty)
            ),
            "ess": self._aggregate_journal(
                corporation_journal.filter(filters.filter_ess)
            ),
            "mining": mining_journal.filter(filters.filter_mining)
            .values("total", "date")
            .aggregate(
                total_amount=Coalesce(Sum(F("total")), 0, output_field=DecimalField()),
                total_amount_day=Coalesce(
                    Sum(F("total"), filter=Q(date__day=self.data.current_date.day)),
                    0,
                    output_field=DecimalField(),
                ),
            ),
            # Calculate Trading
            "contract": self._aggregate_journal(
                character_journal.filter(filters.filter_contract)
            ),
            "transaction": self._aggregate_journal(
                character_journal.filter(filters.filter_market)
            ),
            "donation": self._aggregate_journal(
                character_journal.filter(filters.filter_donation).exclude(
                    first_party_id__in=chars_list
                )
            ),
            # Calculate Costs
            "production_cost": self._aggregate_journal(
                character_journal.filter(filters.filter_production)
            ),
            "market_cost": self._aggregate_journal(
                character_journal.filter(filters.filter_market_cost)
            ),
        }
        # Convert ESS Payout for Character Ledger
        amounts["ess"]["total_amount"] = convert_ess_payout(
            amounts["ess"]["total_amount"]
        )

        return amounts
