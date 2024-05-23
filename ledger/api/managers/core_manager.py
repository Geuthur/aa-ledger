from datetime import datetime

from django.db.models import Q

from ledger import app_settings


class LedgerDataCore:
    """LedgerDataCore class to store the core data."""

    def __init__(self):
        self.total_bounty = 0
        self.total_ess_payout = 0
        self.total_mining = 0
        self.total_miscellaneous = 0
        self.total_isk = 0


class LedgerData(LedgerDataCore):
    """LedgerData class to store the data."""

    def __init__(self):
        super().__init__()
        self.total_cost = 0
        self.total_production_cost = 0
        self.total_market = 0


class LedgerModels:
    """LedgerModels class to store the models."""

    def __init__(
        self, character_journal=None, corporation_journal=None, mining_journal=None
    ):
        self.char_journal = character_journal
        self.corp_journal = corporation_journal
        self.mining_journal = mining_journal


class LedgerDate:
    """LedgerDate class to store the date data."""

    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.monthly = month == 0
        self.current_date = datetime.now()
        self.range_data = 12 if self.monthly else 31
        self.day_checks = list(range(1, self.range_data + 1))


class LedgerSum:
    """LedgerSum class to store the sum amounts."""

    def __init__(self):
        self.sum_amount = ["Ratting"]
        self.sum_amount_ess = ["ESS Payout"]
        self.sum_amount_misc = ["Miscellaneous"]
        self.sum_amount_mining = ["Mining"]
        self.total_sum = None


class LedgerTotal:
    """LedgerTotal class to store the total amounts."""

    def __init__(self):
        self.total_amount = 0
        self.total_amount_ess = 0
        self.total_amount_all = 0
        self.total_amount_mining = 0
        self.total_amount_others = 0

    def to_dict(self):
        """Return the SummaryTotal as a dictionary."""
        return {
            "total_amount": self.total_amount,
            "total_amount_ess": self.total_amount_ess,
            "total_amount_all": self.total_amount_all,
            "total_amount_mining": self.total_amount_mining,
            "total_amount_others": self.total_amount_others,
        }


class LedgerFilterCore:
    """LedgerFilter class to store the filter data."""

    def __init__(self, char_id):
        self.char_id = char_id
        self.filter_first_party = Q(first_party_id__in=self.char_id)
        self.filter_second_party = Q(second_party_id__in=self.char_id)

        self.filter = self.filter_first_party | self.filter_second_party
        self.filter_bounty = self.filter_second_party & Q(ref_type="bounty_prizes")
        self.filter_ess = self.filter_second_party & Q(ref_type="ess_escrow_transfer")
        self.filter_mining = (
            Q(character__eve_character_id__in=char_id)
            if app_settings.LEDGER_MEMBERAUDIT_USE
            else Q(character__character__character_id__in=char_id)
        )


class LedgerFilterCost(LedgerFilterCore):
    """LedgerFilter class to store the filter data."""

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


class LedgerFilterTrading(LedgerFilterCost):
    """LedgerFilter class to store the filter data."""

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


class LedgerFilter(LedgerFilterTrading):
    """LedgerFilterAll class to store all filter data."""

    def __init__(self, char_id):
        super().__init__(char_id)  # Call the __init__ method of the base class
        self.char_id = char_id
