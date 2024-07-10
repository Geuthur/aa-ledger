import calendar
from dataclasses import asdict, dataclass, field
from datetime import datetime

from django.db.models import Q

from ledger import app_settings
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


@dataclass
class LedgerDataCore:
    total_bounty: int = 0
    total_ess_payout: int = 0
    total_mining: int = 0
    total_miscellaneous: int = 0
    total_isk: int = 0


@dataclass
class LedgerData(LedgerDataCore):
    total_cost: int = 0
    total_production_cost: int = 0
    total_market_cost: int = 0


class LedgerModels:
    """LedgerModels class to store the models."""

    def __init__(
        self, character_journal=None, corporation_journal=None, mining_journal=None
    ):
        self.char_journal = character_journal
        self.corp_journal = corporation_journal
        self.mining_journal = mining_journal


@dataclass
class LedgerDate:
    year: int
    month: int
    monthly: bool = field(init=False)
    current_date: datetime = field(default_factory=datetime.now, init=False)
    range_data: int = field(init=False)
    day_checks: list = field(init=False)

    def calculate_days(self):
        _, num_days = calendar.monthrange(self.year, self.month)
        return num_days

    def __post_init__(self):
        self.monthly = self.month == 0
        self.range_data = 12 if self.monthly else self.calculate_days()
        self.day_checks = list(range(1, self.range_data + 1))


@dataclass
class LedgerTotal:
    total_amount: int = 0
    total_amount_ess: int = 0
    total_amount_all: int = 0
    total_amount_mining: int = 0
    total_amount_others: int = 0
    total_amount_costs: int = 0

    def to_dict(self):
        return asdict(self)


@dataclass
class LedgerFilterCore:
    char_id: list

    filter_first_party: Q = field(init=False)
    filter_second_party: Q = field(init=False)
    filter_partys: Q = field(init=False)
    filter_bounty: Q = field(init=False)
    filter_ess: Q = field(init=False)
    filter_mining: Q = field(init=False)
    filter_total: Q = field(init=False)

    def __post_init__(self):
        self.filter_first_party = Q(first_party_id__in=self.char_id)
        self.filter_second_party = Q(second_party_id__in=self.char_id)
        self.filter_partys = self.filter_first_party | self.filter_second_party
        self.filter_total = self.filter_partys & Q(amount__gt=0)
        self.filter_bounty = self.filter_second_party & Q(ref_type="bounty_prizes")
        self.filter_ess = self.filter_second_party & Q(ref_type="ess_escrow_transfer")
        self.filter_mining = (
            Q(character__eve_character__character_id__in=self.char_id)
            if app_settings.LEDGER_MEMBERAUDIT_USE
            else Q(character__character__character_id__in=self.char_id)
        )


@dataclass
class LedgerFilterCost(LedgerFilterCore):
    """LedgerFilter class to store the filter data."""

    def __init__(self, char_id):
        super().__init__(char_id)
        self.filter_market_cost = self.filter_partys & Q(
            ref_type__in=[
                "market_escrow",
                "transaction_tax",
                "market_provider_tax",
                "brokers_fee",
            ],
            amount__lt=0,
        )
        self.filter_production = self.filter_partys & Q(
            ref_type__in=["industry_job_tax", "manufacturing"]
        )
        self.filter_costs = self.filter_partys & Q(amount__lt=0)


@dataclass
class LedgerFilterTrading(LedgerFilterCost):
    """LedgerFilter class to store the filter data."""

    def __init__(self, char_id):
        super().__init__(char_id)
        self.filter_market = self.filter_partys & Q(ref_type="market_transaction")
        self.filter_contract = self.filter_partys & Q(
            ref_type__in=[
                "contract_price_payment_corp",
                "contract_reward",
                "contract_price",
            ],
            amount__gt=0,
        )
        self.filter_donation = self.filter_partys & Q(
            ref_type="player_donation", amount__gt=0
        )


@dataclass
class LedgerFilter(LedgerFilterTrading):
    """LedgerFilterAll class to store all filter data."""

    def __init__(self, char_id):
        super().__init__(char_id)
        self.char_id = char_id
