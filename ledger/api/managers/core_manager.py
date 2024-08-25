import calendar
from dataclasses import asdict, dataclass, field
from datetime import datetime

from django.db.models import Q
from django.utils import timezone

from ledger import app_settings
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)

# Add Filter to LedgerDataCore
# TODO agent_mission_time_bonus_reward, agent_mission_reward


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

    def get_data(self, totals: dict):
        self.total_amount += totals.get("total_amount", 0)
        self.total_amount_ess += totals.get("total_amount_ess", 0)
        self.total_amount_all += totals.get("total_amount_all", 0)
        self.total_amount_mining += totals.get("total_amount_mining", 0)
        self.total_amount_others += totals.get("total_amount_others", 0)
        self.total_amount_costs += totals.get("total_amount_costs", 0)


@dataclass
class LedgerFilterCore:
    char_id: list

    filter_first_party: Q = field(init=False)
    filter_second_party: Q = field(init=False)
    filter_partys: Q = field(init=False)
    filter_total: Q = field(init=False)

    def __post_init__(self):
        self.filter_first_party = Q(first_party_id__in=self.char_id)
        self.filter_second_party = Q(second_party_id__in=self.char_id)
        self.filter_partys = self.filter_first_party | self.filter_second_party
        self.filter_total = self.filter_partys & Q(amount__gt=0)


@dataclass
class LedgerFilterPvE(LedgerFilterCore):

    def __init__(self, char_id):
        super().__init__(char_id)

        self.filter_bounty = self.filter_second_party & Q(ref_type="bounty_prizes")
        self.filter_ess = self.filter_second_party & Q(ref_type="ess_escrow_transfer")
        self.filter_mining = (
            Q(character__eve_character__character_id__in=self.char_id)
            if app_settings.LEDGER_MEMBERAUDIT_USE
            else Q(character__character__character_id__in=self.char_id)
        )

        self.filter_all_pve = self.filter_bounty | self.filter_ess | self.filter_mining

    # TODO add mining filter with aggregate
    def get_all_pve_filters(self):
        return {
            "bounty": self.filter_bounty,
            # "ess": self.filter_ess,
        }

    def get_corp_filters(self):
        return {
            "bounty": self.filter_bounty,
            "ess": self.filter_ess,
        }


# pylint: disable=too-many-instance-attributes
@dataclass
class LedgerFilterCost(LedgerFilterPvE):
    """LedgerFilter class to store the filter data."""

    def __init__(self, char_id):
        super().__init__(char_id)
        self.filter_contract_cost = self.filter_partys & Q(
            ref_type__in=[
                "contract_price_payment_corp",
                "contract_reward",
                "contract_price",
                "contract_collateral",
                "contract_reward_deposited",
            ],
            amount__lt=0,
        )
        self.filter_market_cost = self.filter_partys & Q(
            ref_type__in=[
                "market_escrow",
                "transaction_tax",
                "market_provider_tax",
                "brokers_fee",
            ],
            amount__lt=0,
        )
        self.filter_assets_cost = self.filter_partys & Q(
            ref_type__in=[
                "asset_safety_recovery_tax",
            ],
            amount__lt=0,
        )
        self.filter_traveling_cost = self.filter_partys & Q(
            ref_type__in=[
                "structure_gate_jump",
                "jump_clone_activation_fee",
            ],
            amount__lt=0,
        )
        self.filter_production_cost = self.filter_partys & Q(
            ref_type__in=[
                "industry_job_tax",
                "manufacturing",
                "researching_time_productivity",
                "researching_material_productivity",
                "copying",
                "reprocessing_tax",
                "reaction",
            ],
            amount__lt=0,
        )

        self.filter_skill_cost = self.filter_partys & Q(
            ref_type__in=[
                "skill_purchase",
            ],
            amount__lt=0,
        )

        self.filter_insurance_cost = self.filter_partys & Q(
            ref_type__in=[
                "insurance",
            ],
            amount__lt=0,
        )

        self.filter_planetary_cost = self.filter_partys & Q(
            ref_type__in=[
                "planetary_import_tax",
                "planetary_export_tax",
                "planetary_construction",
            ],
            amount__lt=0,
        )

        self.filter_costs = self.filter_partys & Q(amount__lt=0)

        self.filter_all_costs = (
            self.filter_contract_cost
            | self.filter_market_cost
            | self.filter_assets_cost
            | self.filter_traveling_cost
            | self.filter_production_cost
            | self.filter_skill_cost
            | self.filter_insurance_cost
            | self.filter_planetary_cost
        )

    def get_all_costs_filters(self):
        return {
            "market_cost": self.filter_market_cost,
            "production_cost": self.filter_production_cost,
            "contract_cost": self.filter_contract_cost,
            "traveling_cost": self.filter_traveling_cost,
            "asset_cost": self.filter_assets_cost,
            "skill_cost": self.filter_skill_cost,
            "insurance_cost": self.filter_insurance_cost,
            "planetary_cost": self.filter_planetary_cost,
        }


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

        self.filter_insurance = self.filter_second_party & Q(
            ref_type__in=[
                "insurance",
            ],
            amount__gt=0,
        )

        self.filter_all_misc = (
            self.filter_market | self.filter_contract | self.filter_insurance
        )

    def get_all_misc_filters(self, chars_list):
        return {
            "transaction": self.filter_market,
            "contract": self.filter_contract,
            "donation": self.filter_donation & ~Q(first_party_id__in=chars_list),
            "insurance": self.filter_insurance,
        }


@dataclass
class LedgerFilterMission(LedgerFilterTrading):
    """LedgerFilterMission class to store the filter data."""

    def __init__(self, char_id):
        super().__init__(char_id)
        self.filter_mission = self.filter_partys & Q(
            ref_type__in=[
                "agent_mission_reward",
                "agent_mission_time_bonus_reward",
            ],
            amount__gt=0,
        )

        self.loyality_points_cost = self.filter_partys & Q(
            ref_type="lp_store", amount__lt=0
        )

        self.filter_all_missions = self.filter_mission | self.loyality_points_cost

    def get_all_mission_filters(self):
        return {
            "mission": self.filter_mission,
            "loyality_point_cost": self.loyality_points_cost,
        }


@dataclass
class LedgerFilter(LedgerFilterMission):
    """LedgerFilterAll class to store all filter data."""

    def __init__(self, char_id):
        super().__init__(char_id)
        self.char_id = char_id

    def get_all_filters(self, chars_list):
        filters = {}
        filters.update(self.get_all_pve_filters())
        filters.update(self.get_all_costs_filters())
        filters.update(self.get_all_misc_filters(chars_list))
        filters.update(self.get_all_mission_filters())
        return filters
