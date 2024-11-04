from collections import defaultdict
from decimal import Decimal

from django.db import models
from django.db.models import Case, DecimalField, F, Q, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce
from django.utils import timezone

from ledger.hooks import get_extension_logger
from ledger.view_helpers.core import events_filter

logger = get_extension_logger(__name__)
# PvE - Income
BOUNTY_PRIZES = ["bounty_prizes"]
ESS_TRANSFER = ["ess_escrow_transfer"]
MISSION_REWARD = ["agent_mission_reward", "agent_mission_time_bonus_reward"]
INCURSION = ["corporate_reward_payout"]

# Cost Ref Types
CONTRACT_COST = [
    "contract_price_payment_corp",
    "contract_reward",
    "contract_price",
    "contract_collateral",
    "contract_reward_deposited",
]
MARKET_COST = ["market_escrow", "transaction_tax", "market_provider_tax", "brokers_fee"]
ASSETS_COST = ["asset_safety_recovery_tax"]
TRAVELING_COST = [
    "structure_gate_jump",
    "jump_clone_activation_fee",
    "jump_clone_installation_fee",
]
PRODUCTION_COST = [
    "industry_job_tax",
    "manufacturing",
    "researching_time_productivity",
    "researching_material_productivity",
    "copying",
    "reprocessing_tax",
    "reaction",
]
SKILL_COST = ["skill_purchase"]
INSURANCE_COST = ["insurance"]
PLANETARY_COST = [
    "planetary_export_tax",
    "planetary_import_tax",
    "planetary_construction",
]
LP_COST = ["lp_store"]
# Trading
MARKET_INCOME = ["market_transaction", "market_escrow"]
CONTRACT_INCOME = [
    "contract_price_payment_corp",
    "contract_reward",
    "contract_price",
    "contract_reward_refund",
]
DONATION_INCOME = ["player_donation"]
INSURANCE_INCOME = ["insurance"]
# MISC
CORP_PROJECTS = ["milestone_reward_payment"]  # Not Confirmed
DAILY_GOAL_REWARD = ["daily_goal_payouts"]

# PVE
BOUNTY_FILTER = Q(ref_type__in=BOUNTY_PRIZES)
MISSION_FILTER = Q(ref_type__in=MISSION_REWARD)
ESS_FILTER = Q(ref_type__in=ESS_TRANSFER)
INCURSION_FILTER = Q(ref_type__in=INCURSION)
# COSTS
CONTRACT_COST_FILTER = Q(ref_type__in=CONTRACT_COST, amount__lt=0)
MARKET_COST_FILTER = Q(ref_type__in=MARKET_COST, amount__lt=0)
ASSETS_COST_FILTER = Q(ref_type__in=ASSETS_COST, amount__lt=0)
TRAVELING_COST_FILTER = Q(ref_type__in=TRAVELING_COST, amount__lt=0)
PRODUCTION_COST_FILTER = Q(ref_type__in=PRODUCTION_COST, amount__lt=0)
SKILL_COST_FILTER = Q(ref_type__in=SKILL_COST, amount__lt=0)
INSURANCE_COST_FILTER = Q(ref_type__in=INSURANCE_COST, amount__lt=0)
PLANETARY_COST_FILTER = Q(ref_type__in=PLANETARY_COST, amount__lt=0)
LP_COST_FILTER = Q(ref_type__in=LP_COST, amount__lt=0)
# TRADES
MARKET_INCOME_FILTER = Q(ref_type__in=MARKET_INCOME, amount__gt=0)
CONTRACT_INCOME_FILTER = Q(ref_type__in=CONTRACT_INCOME, amount__gt=0)
DONATION_INCOME_FILTER = Q(ref_type__in=DONATION_INCOME, amount__gt=0)
INSURANCE_INCOME_FILTER = Q(ref_type__in=INSURANCE_INCOME, amount__gt=0)
CORP_PROJECTS_FILTER = Q(ref_type__in=CORP_PROJECTS, amount__gt=0)
DAILY_GOAL_REWARD_FILTER = Q(ref_type__in=DAILY_GOAL_REWARD, amount__gt=0)

PVE_FILTER = BOUNTY_FILTER | ESS_FILTER
MISC_FILTER = (
    MARKET_INCOME_FILTER
    | CONTRACT_INCOME_FILTER
    | INSURANCE_INCOME_FILTER
    | MISSION_FILTER
    | CORP_PROJECTS_FILTER
    | INCURSION_FILTER
    | DAILY_GOAL_REWARD_FILTER
)
COST_FILTER = (
    CONTRACT_COST_FILTER
    | MARKET_COST_FILTER
    | ASSETS_COST_FILTER
    | TRAVELING_COST_FILTER
    | PRODUCTION_COST_FILTER
    | SKILL_COST_FILTER
    | INSURANCE_COST_FILTER
    | PLANETARY_COST_FILTER
    | LP_COST_FILTER
)


class CharWalletQueryFilter(models.QuerySet):
    # PvE - Income
    def annotate_bounty(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_bounty=Coalesce(
                Sum(
                    "amount",
                    Q(ref_type__in=BOUNTY_PRIZES, second_party_id__in=character_ids),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def filter_ess(self, character_ids: list, filter_date=None) -> models.QuerySet:
        # pylint: disable=import-outside-toplevel
        from ledger.models.corporationaudit import CorporationWalletJournalEntry

        qs = CorporationWalletJournalEntry.objects.get_queryset()

        if filter_date:
            qs = qs.filter(filter_date)

        qs = events_filter(qs)

        qs = qs.filter(ref_type__in=ESS_TRANSFER, second_party_id__in=character_ids)

        qs = qs.annotate(
            total_ess=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )
        return qs

    def filter_daily_goal(
        self, character_ids: list, filter_date=None
    ) -> models.QuerySet:
        # pylint: disable=import-outside-toplevel
        from ledger.models.corporationaudit import CorporationWalletJournalEntry

        qs = CorporationWalletJournalEntry.objects.get_queryset()

        if filter_date:
            qs = qs.filter(filter_date)

        qs = events_filter(qs)

        qs = qs.filter(
            ref_type__in=DAILY_GOAL_REWARD, second_party_id__in=character_ids
        )

        qs = qs.annotate(
            total_daily_goal=Coalesce(
                Sum("amount"), Value(0), output_field=DecimalField()
            )
        )
        return qs

    def annotate_mission(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_mission=Coalesce(
                Sum(
                    "amount",
                    Q(
                        MISSION_FILTER,
                        second_party_id__in=character_ids,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_mining(self, character_ids: list, filter_date=None) -> models.QuerySet:
        # pylint: disable=import-outside-toplevel
        from ledger.models.characteraudit import CharacterMiningLedger

        qs = CharacterMiningLedger.objects.get_queryset()

        qs = qs.filter(character__character__character_id__in=character_ids)

        if filter_date:
            qs = qs.filter(filter_date)

        return qs.annotate_pricing().values(
            "character__character__character_id", "total"
        )

    # Costs
    def annotate_contract_cost(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_contract_cost=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        CONTRACT_COST_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_market_cost(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_market_cost=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        MARKET_COST_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_assets_cost(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_assets_cost=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        ASSETS_COST_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_traveling_cost(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_traveling_cost=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        TRAVELING_COST_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_production_cost(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_production_cost=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        PRODUCTION_COST_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_skill_cost(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_skill_cost=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        SKILL_COST_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_insurance_cost(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_insurance_cost=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        INSURANCE_COST_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_planetary_cost(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_planetary_cost=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        PLANETARY_COST_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_lp_cost(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_lp=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        LP_COST_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    # Trading - Income
    def annotate_market_income(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_market_income=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        MARKET_INCOME_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_contract_income(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_contract_income=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        CONTRACT_INCOME_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_donation_income(
        self, character_ids: list, exclude=None
    ) -> models.QuerySet:
        qs = self

        if exclude:
            qs = qs.exclude(first_party_id__in=exclude)

        return qs.annotate(
            total_donation_income=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        DONATION_INCOME_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_insurance_income(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_insurance_income=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        INSURANCE_INCOME_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_corporation_projects_income(
        self, character_ids: list
    ) -> models.QuerySet:
        return self.annotate(
            total_cproject_income=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        CORP_PROJECTS_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )


class CharWalletQuerySet(CharWalletQueryFilter):
    # Supports Member Audit Intigration
    def generate_ledger(
        self, character_ids: list, filter_date=None, exclude=None
    ) -> models.QuerySet:
        """Generate the Ledger for the given characters."""

        # Filter Characters
        qs = self.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids)
        )

        if filter_date:
            qs = qs.filter(filter_date)

        # Subquery to identify entry_ids in total_contract_income
        contract_income_entry_ids = qs.filter(CONTRACT_INCOME_FILTER).values("entry_id")

        # Aggregate the results directly from the original fields
        ledger_data = qs.aggregate(
            # PvE
            total_bounty=Sum("amount", filter=BOUNTY_FILTER),
            total_mission=Sum("amount", filter=MISSION_FILTER),
            total_incursion_income=Sum("amount", filter=INCURSION_FILTER),
            total_lp=Sum("amount", filter=LP_COST_FILTER),
            # Costs
            total_contract_cost=Sum(
                "amount",
                filter=CONTRACT_COST_FILTER
                & ~Q(entry_id__in=Subquery(contract_income_entry_ids)),
            ),
            total_market_cost=Sum("amount", filter=MARKET_COST_FILTER),
            total_assets_cost=Sum("amount", filter=ASSETS_COST_FILTER),
            total_traveling_cost=Sum("amount", filter=TRAVELING_COST_FILTER),
            total_production_cost=Sum("amount", filter=PRODUCTION_COST_FILTER),
            total_skill_cost=Sum("amount", filter=SKILL_COST_FILTER),
            total_insurance_cost=Sum("amount", filter=INSURANCE_COST_FILTER),
            total_planetary_cost=Sum("amount", filter=PLANETARY_COST_FILTER),
            # Misc Income
            total_market_income=Sum("amount", filter=MARKET_INCOME_FILTER),
            total_contract_income=Sum("amount", filter=CONTRACT_INCOME_FILTER),
            total_insurance_income=Sum("amount", filter=INSURANCE_INCOME_FILTER),
            total_donation_income=Sum(
                "amount",
                filter=(
                    DONATION_INCOME_FILTER & ~Q(first_party_id__in=exclude)
                    if exclude is not None
                    else DONATION_INCOME_FILTER
                ),
            ),
            total_cproject_income=Sum("amount", filter=CORP_PROJECTS_FILTER),
        )

        # Special cases
        ess_data = self.filter_ess(character_ids, filter_date).aggregate(
            total_ess=Sum("amount")
        )
        mining_data = self.annotate_mining(character_ids, filter_date).aggregate(
            total_mining=Sum("total")
        )

        # NOT IMPLEMENTED
        # NOTE: Can not calculate Stolen ESS atm
        # ESS Amounts per Char Journal
        # ess = (Decimal(ledger_data["total_bounty"] or 0) / 100) * Decimal(66.6667)

        amounts = {
            "bounty": Decimal(ledger_data["total_bounty"] or 0),
            "ess": Decimal(ess_data["total_ess"] or 0),
            "mining": Decimal(mining_data["total_mining"] or 0),
            "mission": Decimal(ledger_data["total_mission"] or 0),
            "incursion": Decimal(ledger_data["total_incursion_income"] or 0),
            "insurance": Decimal(ledger_data["total_insurance_income"] or 0),
        }

        amounts_others = {
            "donation": Decimal(ledger_data["total_donation_income"] or 0),
            "transaction": Decimal(ledger_data["total_market_income"] or 0),
            "contract": Decimal(ledger_data["total_contract_income"] or 0),
            "cproject": Decimal(ledger_data["total_cproject_income"] or 0),
        }

        amounts_costs = {
            "contract_cost": Decimal(ledger_data["total_contract_cost"] or 0),
            "market_cost": Decimal(ledger_data["total_market_cost"] or 0),
            "assets_cost": Decimal(ledger_data["total_assets_cost"] or 0),
            "traveling_cost": Decimal(ledger_data["total_traveling_cost"] or 0),
            "production_cost": Decimal(ledger_data["total_production_cost"] or 0),
            "skill_cost": Decimal(ledger_data["total_skill_cost"] or 0),
            "insurance_cost": Decimal(ledger_data["total_insurance_cost"] or 0),
            "planetary_cost": Decimal(ledger_data["total_planetary_cost"] or 0),
            "lp_cost": Decimal(ledger_data["total_lp"] or 0),
        }

        return {
            "amounts": amounts,
            "amounts_others": amounts_others,
            "amounts_costs": amounts_costs,
        }

    def generate_template(
        self,
        amounts: defaultdict,
        character_ids: list,
        filter_date: timezone.datetime,
        exclude=None,
    ) -> dict:
        """Generate the Billboard for the given characters."""
        qs = self.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids)
        )

        # Subquery to identify entry_ids in contract filter
        contract_entry_ids = qs.filter(CONTRACT_INCOME_FILTER).values("entry_id")

        # Define the types and their respective filters
        types_filters = {
            # PvE
            "bounty": BOUNTY_FILTER,
            "mission": MISSION_FILTER,
            "incursion": INCURSION_FILTER,
            "loyality_point_cost": LP_COST_FILTER,
            "insurance": INSURANCE_INCOME_FILTER,
            # Costs
            "market_cost": MARKET_COST_FILTER,
            "production_cost": PRODUCTION_COST_FILTER,
            "contract_cost": CONTRACT_COST_FILTER
            & ~Q(entry_id__in=Subquery(contract_entry_ids)),
            "traveling_cost": TRAVELING_COST_FILTER,
            "asset_cost": ASSETS_COST_FILTER,
            "skill_cost": SKILL_COST_FILTER,
            "insurance_cost": INSURANCE_COST_FILTER,
            "planetary_cost": PLANETARY_COST_FILTER,
            # Income
            "transaction": MARKET_INCOME_FILTER,
            "contract": CONTRACT_INCOME_FILTER,
            "donation": (
                DONATION_INCOME_FILTER & ~Q(first_party_id__in=exclude)
                if exclude is not None
                else DONATION_INCOME_FILTER
            ),
            "cproject": CORP_PROJECTS_FILTER,
        }

        # Annotate the queryset with the sums for each type
        # NOTE: TAX Field is only for Bounty and work atm
        annotations = {}
        for type_name, type_filter in types_filters.items():
            annotations[f"{type_name}_total_amount"] = Coalesce(
                Sum(
                    Case(
                        When(
                            type_filter,
                            then=F("amount"),
                        )
                    )
                ),
                Value(0),
                output_field=DecimalField(),
            )
            annotations[f"{type_name}_total_amount_day"] = Coalesce(
                Sum(
                    Case(
                        When(
                            type_filter
                            & Q(
                                date__year=filter_date.year,
                                date__month=filter_date.month,
                                date__day=filter_date.day,
                            ),
                            then=F("amount"),
                        )
                    )
                ),
                Value(0),
                output_field=DecimalField(),
            )
            annotations[f"{type_name}_total_amount_hour"] = Coalesce(
                Sum(
                    Case(
                        When(
                            type_filter
                            & Q(
                                date__year=filter_date.year,
                                date__month=filter_date.month,
                                date__day=filter_date.day,
                                date__hour=filter_date.hour,
                            ),
                            then=F("amount"),
                        )
                    )
                ),
                Value(0),
                output_field=DecimalField(),
            )

        qs = qs.aggregate(**annotations)

        # Assign the results to the amounts dictionary
        for type_name in types_filters:
            amounts[type_name]["total_amount"] = qs[f"{type_name}_total_amount"]
            amounts[type_name]["total_amount_day"] = qs[f"{type_name}_total_amount_day"]
            amounts[type_name]["total_amount_hour"] = qs[
                f"{type_name}_total_amount_hour"
            ]
        return amounts

    def annotate_billboard(self, chars: list, alts: list) -> models.QuerySet:
        qs = self.filter(Q(first_party_id__in=chars) | Q(second_party_id__in=chars))
        return qs.annotate(
            total_bounty=Coalesce(
                Sum(
                    F("amount"),
                    filter=Q(ref_type__in=BOUNTY_PRIZES, second_party_id__in=chars),
                ),
                Value(0),
                output_field=DecimalField(),
            ),
            total_miscellaneous=Coalesce(
                Sum(
                    "amount",
                    filter=MISC_FILTER
                    | (DONATION_INCOME_FILTER & ~Q(first_party_id__in=alts)),
                ),
                Value(0),
                output_field=DecimalField(),
            ),
            total_cost=Coalesce(
                Sum(
                    "amount",
                    filter=COST_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            ),
            total_market_cost=Coalesce(
                Sum(
                    "amount",
                    filter=MARKET_COST_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            ),
            total_production_cost=Coalesce(
                Sum(
                    "amount",
                    filter=PRODUCTION_COST_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            ),
        )


class CharWalletManagerBase(models.Manager):
    pass


CharWalletManager = CharWalletManagerBase.from_queryset(CharWalletQuerySet)
