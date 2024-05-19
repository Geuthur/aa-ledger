from datetime import datetime

from django.db.models import DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce

from ledger import app_settings
from ledger.api.helpers import (
    get_alts_queryset,
    get_main_and_alts_all,
    get_main_character,
    get_models_and_string,
)
from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import CorporationWalletJournalEntry
from ledger.view_helpers.core import calculate_days_year, events_filter

CharacterMiningLedger, CharacterWalletJournalEntry, SR_CHAR = get_models_and_string()

logger = get_extension_logger(__name__)


class TemplateFilterCore:
    """TemplateFilter class to store the filter data."""

    def __init__(self, char_id):
        self.char_id = char_id
        self.filter = Q(second_party_id__in=self.char_id) | Q(
            first_party_id__in=self.char_id
        )
        self.filter_bounty = self.filter & Q(ref_type="bounty_prizes")
        self.filter_ess = self.filter & Q(ref_type="ess_escrow_transfer")
        self.filter_mining = Q(character__eve_character__character_id__in=self.char_id)


class TemplateFilterCost(TemplateFilterCore):
    """TemplateFilter class to store the filter data."""

    def __init__(self, char_id):
        super().__init__(char_id)
        self.my_filter_market_cost = self.filter & Q(
            ref_type__in=[
                "transaction_tax",
                "market_provider_tax",
                "brokers_fee",
            ]
        )
        self.filter_production = self.filter & Q(
            ref_type__in=["industry_job_tax", "manufacturing"]
        )


class TemplateFilterTrading(TemplateFilterCost):
    """TemplateFilter class to store the filter data."""

    # pylint: disable=duplicate-code
    def __init__(self, char_id):
        super().__init__(char_id)
        self.filter_market = self.filter & Q(ref_type="market_transaction")
        self.filter_contract = self.filter & Q(
            ref_type__in=[
                "contract_price_payment_corp",
                "contract_reward",
                "contract_price",
            ],
            amount__gt=0,
        )
        self.filter_donation = self.filter & Q(ref_type="player_donation")


class TemplateFilter(TemplateFilterTrading):
    """TemplateFilterAll class to store all filter data."""

    def __init__(self, char_id):
        super().__init__(char_id)  # Call the __init__ method of the base class
        self.char_id = char_id


class TemplateData:
    """TemplateData class to store the data."""

    def __init__(self, request, request_id, year, month):
        self.request = request
        self.request_id = request_id
        self.year = year
        self.month = month
        self.current_date = datetime.now()
        self.current_date = self.current_date.replace(year=self.year)
        if not self.month == 0:
            self.current_date = self.current_date.replace(month=self.month)


class TemplateTotalCore:
    def __init__(self):
        self.ess = 0
        self.mining = 0
        self.contract = 0
        self.transaction = 0
        self.donation = 0
        self.production_cost = 0
        self.market_cost = 0


class TemplateTotalDay:
    def __init__(self):
        self.ess_day = 0
        self.mining_day = 0
        self.contract_day = 0
        self.transaction_day = 0
        self.donation_day = 0
        self.production_cost_day = 0
        self.market_cost_day = 0


class TemplateTotalHour:
    def __init__(self):
        self.ess_hour = 0
        self.mining_hour = 0
        self.contract_hour = 0
        self.transaction_hour = 0
        self.donation_hour = 0
        self.production_cost_hour = 0
        self.market_cost_hour = 0


class TemplateTotal(TemplateTotalCore, TemplateTotalDay, TemplateTotalHour):
    def __init__(self):
        self.bounty = 0
        self.bounty_day = 0
        self.bounty_hour = 0
        TemplateTotalCore.__init__(self)
        TemplateTotalDay.__init__(self)
        TemplateTotalHour.__init__(self)

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
        filters = (
            Q(character__eve_character__in=self.chars)
            if app_settings.LEDGER_MEMBERAUDIT_USE
            else Q(character__character__in=self.chars)
        )
        filter_date = Q(date__year=self.data.year)
        if not self.data.month == 0:
            filter_date &= Q(date__month=self.data.month)

        chars = [char.character_id for char in self.chars]

        entries_filter = Q(second_party_id__in=chars) | Q(first_party_id__in=chars)

        # Filter the entries for the current day/month
        character_journal = (
            CharacterWalletJournalEntry.objects.filter(filters, filter_date)
            .select_related("first_party", "second_party", SR_CHAR)
            .order_by("-date")
        )

        corporation_journal = (
            CorporationWalletJournalEntry.objects.filter(entries_filter, filter_date)
            .select_related("first_party", "second_party")
            .order_by("-date")
        )

        # Exclude Events to avoid wrong stats
        corporation_journal = events_filter(corporation_journal)
        mining_journal = (
            CharacterMiningLedger.objects.filter(filters, filter_date)
            .select_related(SR_CHAR)
            .order_by("-date")
        ).annotate_pricing()

        self._process_characters(character_journal, corporation_journal, mining_journal)
        logger.debug(self.template_dict)
        return self.template_dict

    def corporation_template(self):
        """
        Create the corporation template.
        return: dict
        """

        mains, chars = get_main_and_alts_all(self.chars, char_ids=True)

        filters = Q(second_party_id__in=chars)
        filter_date = Q(date__year=self.data.year)
        if not self.data.month == 0:
            filter_date &= Q(date__month=self.data.month)

        corporation_journal = (
            CorporationWalletJournalEntry.objects.filter(filters, filter_date)
            .select_related("first_party", "second_party", "division")
            .values("amount", "date", "second_party_id", "ref_type")
            .order_by("-date")
        )

        if self.show_year:
            mains_data = mains
        else:
            mains_data = {self.data.request_id: mains.get(self.data.request_id, None)}

        # Exclude Events to avoid wrong stats
        corporation_journal = events_filter(corporation_journal)

        self._process_corporation(corporation_journal, mains_data)
        return self.template_dict

    # Process the character
    def _process_characters(
        self, character_journal, corporation_journal, mining_journal
    ):
        """Process the characters."""
        _, main = get_main_character(self.data.request, self.data.request_id)

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
    def _process_corporation(self, corporation_journal, mains_data):
        """Process the characters."""

        total_amounts = {
            "bounty": {
                "total_amount": 0,
                "total_amount_day": 0,
                "total_amount_hour": 0,
            },
            "ess": {"total_amount": 0, "total_amount_day": 0, "total_amount_hour": 0},
        }

        for _, main_data in mains_data.items():
            main = main_data["main"]
            alts = main_data["alts"]

            # Each Chars from a Main Character
            chars = [alt.character_id for alt in alts] + [main.character_id]

            filters = TemplateFilter(chars)

            amounts = {
                # Calculate Income
                "bounty": self._aggregate_journal(
                    corporation_journal.filter(filters.filter_bounty)
                ),
                "ess": self._aggregate_journal(
                    corporation_journal.filter(filters.filter_ess)
                ),
            }

            # Add amounts to total_amounts
            for key, value in amounts.items():
                for sub_key, sub_value in value.items():
                    total_amounts[key][sub_key] += sub_value

            self._update_template_dict(main)

        self._generate_amounts_dict(total_amounts)

    # Aggregate Journal
    def _aggregate_journal(self, journal):
        result = journal.aggregate(
            total_amount=Coalesce(Sum(F("amount")), 0, output_field=DecimalField()),
            total_amount_day=Coalesce(
                Sum(F("amount"), filter=Q(date__day=self.data.current_date.day)),
                0,
                output_field=DecimalField(),
            ),
            total_amount_hour=Coalesce(
                Sum(
                    F("amount"),
                    filter=Q(
                        date__day=self.data.current_date.day,
                        date__hour=self.data.current_date.hour,
                    ),
                ),
                0,
                output_field=DecimalField(),
            ),
        )
        return result

    # Update Core Dict
    def _update_template_dict(self, char):
        main_name = char.character_name if not self.show_year else "Summary"
        main_id = char.character_id if not self.show_year else 0
        date = (
            str(self.data.current_date.year)
            if self.data.month == 0
            else self.data.current_date.strftime("%B")
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
        current_day = (
            calculate_days_year()
            if self.data.month == 0
            else self.data.current_date.day
        )
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
                            if amounts[key]["total_amount_day"] is not None
                            else None
                        ),
                        "total_amount_hour": (
                            round(amounts[key]["total_amount_hour"], 2)
                            if key != "mining"
                            and amounts[key]["total_amount_hour"] is not None
                            else None
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
    def _process_amounts_char(self, char, models, chars_list):
        char_id = char.character_id

        # Create the filters
        filters = TemplateFilter([char_id])

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
                character_journal.filter(filters.my_filter_market_cost)
            ),
        }

        # Apply formula to amounts["ess"]["total_amount"]
        amounts["ess"]["total_amount"] = (
            amounts["ess"]["total_amount"] / app_settings.LEDGER_CORP_TAX
        ) * (100 - app_settings.LEDGER_CORP_TAX)

        return amounts
