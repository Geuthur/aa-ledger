import calendar
from dataclasses import asdict, dataclass, field
from datetime import datetime

from django.utils import timezone

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
    current_date: datetime = None
    range_data: int = field(init=False)
    day_checks: list = field(init=False)

    def calculate_days(self):
        _, num_days = calendar.monthrange(self.year, self.month)
        return num_days

    def __post_init__(self):
        self.current_date = timezone.now()
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

    def get_summary(self, totals: dict):
        self.total_amount += totals.get("total_amount", 0)
        self.total_amount_ess += totals.get("total_amount_ess", 0)
        self.total_amount_all += totals.get("total_amount_all", 0)
        self.total_amount_mining += totals.get("total_amount_mining", 0)
        self.total_amount_others += totals.get("total_amount_others", 0)
        self.total_amount_costs += totals.get("total_amount_costs", 0)
