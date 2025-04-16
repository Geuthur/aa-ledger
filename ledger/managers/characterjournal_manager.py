import logging

from django.db import models
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce

from ledger.constants import (
    ASSETS,
    BOUNTY_PRIZES,
    CONTRACT,
    DAILY_GOAL_REWARD,
    DONATION,
    ESS_TRANSFER,
    INCURSION,
    INSURANCE,
    LP,
    MARKET,
    MILESTONE_REWARD,
    MISSION_REWARD,
    PLANETARY,
    PRODUCTION,
    SKILL,
    TRAVELING,
)

logger = logging.getLogger(__name__)

# PVE
BOUNTY_FILTER = Q(ref_type__in=BOUNTY_PRIZES)
MISSION_FILTER = Q(ref_type__in=MISSION_REWARD)
ESS_FILTER = Q(ref_type__in=ESS_TRANSFER)
INCURSION_FILTER = Q(ref_type__in=INCURSION)
DAILY_GOAL_REWARD_FILTER = Q(ref_type__in=DAILY_GOAL_REWARD, amount__gt=0)
# COSTS
CONTRACT_COST_FILTER = Q(ref_type__in=CONTRACT, amount__lt=0)
MARKET_COST_FILTER = Q(ref_type__in=MARKET, amount__lt=0)
ASSETS_COST_FILTER = Q(ref_type__in=ASSETS, amount__lt=0)
TRAVELING_COST_FILTER = Q(ref_type__in=TRAVELING, amount__lt=0)
PRODUCTION_COST_FILTER = Q(ref_type__in=PRODUCTION, amount__lt=0)
SKILL_COST_FILTER = Q(ref_type__in=SKILL, amount__lt=0)
INSURANCE_COST_FILTER = Q(ref_type__in=INSURANCE, amount__lt=0)
PLANETARY_COST_FILTER = Q(ref_type__in=PLANETARY, amount__lt=0)
LP_COST_FILTER = Q(ref_type__in=LP, amount__lt=0)
# TRADES
MARKET_INCOME_FILTER = Q(ref_type__in=MARKET, amount__gt=0)
CONTRACT_INCOME_FILTER = Q(ref_type__in=CONTRACT, amount__gt=0)
DONATION_INCOME_FILTER = Q(ref_type__in=DONATION, amount__gt=0)
INSURANCE_INCOME_FILTER = Q(ref_type__in=INSURANCE, amount__gt=0)
MILESTONE_REWARD_FILTER = Q(ref_type__in=MILESTONE_REWARD, amount__gt=0)

PVE_FILTER = BOUNTY_FILTER | ESS_FILTER
MISC_FILTER = (
    MARKET_INCOME_FILTER
    | INSURANCE_INCOME_FILTER
    | MISSION_FILTER
    | INCURSION_FILTER
    | MILESTONE_REWARD_FILTER
)
COST_FILTER = (
    MARKET_COST_FILTER
    | PRODUCTION_COST_FILTER
    | CONTRACT_COST_FILTER
    | LP_COST_FILTER
    | TRAVELING_COST_FILTER
    | ASSETS_COST_FILTER
    | SKILL_COST_FILTER
    | INSURANCE_COST_FILTER
    | PLANETARY_COST_FILTER
)


class CharWalletIncomeFilter(models.QuerySet):
    # PvE - Income
    def annotate_bounty_income(self) -> models.QuerySet:
        return self.annotate(
            bounty_income=Coalesce(
                Sum(
                    "amount",
                    filter=BOUNTY_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_mission_income(self) -> models.QuerySet:
        return self.annotate(
            mission_income=Coalesce(
                Sum(
                    "amount",
                    filter=MISSION_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_incursion_income(self) -> models.QuerySet:
        return self.annotate(
            incursion_income=Coalesce(
                Sum(
                    "amount",
                    filter=INCURSION_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    # Trading - Income
    def annotate_market_income(self) -> models.QuerySet:
        return self.annotate(
            market_income=Coalesce(
                Sum(
                    "amount",
                    filter=MARKET_INCOME_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_contract_income(self) -> models.QuerySet:
        return self.annotate(
            contract_income=Coalesce(
                Sum(
                    "amount",
                    filter=CONTRACT_INCOME_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_donation_income(self, exclude: list = None) -> models.QuerySet:
        if exclude is None:
            exclude = []

        return self.annotate(
            donation_income=Coalesce(
                Sum(
                    "amount",
                    filter=Q(DONATION_INCOME_FILTER) & ~Q(first_party_id__in=exclude),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_insurance_income(self) -> models.QuerySet:
        return self.annotate(
            insurance_income=Coalesce(
                Sum(
                    "amount",
                    filter=INSURANCE_INCOME_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_milestone_income(self) -> models.QuerySet:
        return self.annotate(
            milestone_income=Coalesce(
                Sum(
                    "amount",
                    filter=MILESTONE_REWARD_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )


class CharWalletOutSideFilter(CharWalletIncomeFilter):
    def annotate_miscellaneous(self) -> models.QuerySet:
        return self.annotate(
            miscellaneous=Coalesce(
                Sum(
                    "amount",
                    filter=MISC_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_miscellaneous_with_exclude(self, exclude=None) -> models.QuerySet:
        """Annotate all income together"""
        qs = (
            self.annotate_donation_income(exclude=exclude)
            .annotate_mission_income()
            .annotate_milestone_income()
            .annotate_insurance_income()
            .annotate_market_income()
            .annotate_contract_income()
            .annotate_incursion_income()
        )
        return qs.annotate(
            miscellaneous=Coalesce(
                F("mission_income")
                + F("incursion_income")
                + F("insurance_income")
                + F("market_income")
                + F("contract_income")
                + F("donation_income")
                + F("milestone_income"),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_costs(self) -> models.QuerySet:
        return self.annotate(
            costs=Coalesce(
                Sum(
                    "amount",
                    filter=COST_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )


class CharWalletCostQueryFilter(CharWalletOutSideFilter):
    # Costs
    def annotate_contract_cost(self) -> models.QuerySet:
        return self.annotate(
            contract_cost=Coalesce(
                Sum(
                    "amount",
                    filter=CONTRACT_COST_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_market_cost(self) -> models.QuerySet:
        return self.annotate(
            market_cost=Coalesce(
                Sum(
                    "amount",
                    filter=MARKET_COST_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_asset_cost(self) -> models.QuerySet:
        return self.annotate(
            asset_cost=Coalesce(
                Sum(
                    "amount",
                    filter=ASSETS_COST_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_traveling_cost(self) -> models.QuerySet:
        return self.annotate(
            traveling_cost=Coalesce(
                Sum(
                    "amount",
                    filter=TRAVELING_COST_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_production_cost(self) -> models.QuerySet:
        return self.annotate(
            production_cost=Coalesce(
                Sum(
                    "amount",
                    filter=PRODUCTION_COST_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_skill_cost(self) -> models.QuerySet:
        return self.annotate(
            skill_cost=Coalesce(
                Sum(
                    "amount",
                    filter=SKILL_COST_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_insurance_cost(self) -> models.QuerySet:
        return self.annotate(
            insurance_cost=Coalesce(
                Sum(
                    "amount",
                    filter=INSURANCE_COST_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_planetary_cost(self) -> models.QuerySet:
        return self.annotate(
            planetary_cost=Coalesce(
                Sum(
                    "amount",
                    filter=PLANETARY_COST_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_lp_cost(self) -> models.QuerySet:
        return self.annotate(
            lp_cost=Coalesce(
                Sum(
                    "amount",
                    filter=LP_COST_FILTER,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )


class CharWalletQuerySet(CharWalletCostQueryFilter):
    pass


class CharWalletManagerBase(models.Manager):
    pass


CharWalletManager = CharWalletManagerBase.from_queryset(CharWalletQuerySet)
