# Standard Library
from decimal import Decimal

# Django
from django.db import models
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce, Round

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__, app_settings
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
    MISSION_REWARD,
    PRODUCTION,
    RENTAL,
    SKILL,
    TRAVELING,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

# Filters
BOUNTY_FILTER = Q(ref_type__in=BOUNTY_PRIZES, amount__gt=0)
ESS_FILTER = Q(ref_type__in=ESS_TRANSFER, amount__gt=0)
INCURSION_FILTER = Q(ref_type__in=INCURSION, amount__gt=0)
MISSION_FILTER = Q(ref_type__in=MISSION_REWARD, amount__gt=0)
DAILY_GOAL_REWARD_FILTER = Q(ref_type__in=DAILY_GOAL_REWARD, amount__gt=0)
CITADEL_FILTER = Q(ref_type__in=PRODUCTION, amount__gt=0)

MISC_FILTER = Q(
    ref_type__in=[
        *ASSETS,
        *CONTRACT,
        *DAILY_GOAL_REWARD,
        *DONATION,
        *INCURSION,
        *INSURANCE,
        *MISSION_REWARD,
        *PRODUCTION,
        *MARKET,
        *TRAVELING,
        *LP,
    ],
    amount__gt=0,
)

COSTS_FILTER = Q(
    ref_type__in=[
        *ASSETS,
        *CONTRACT,
        *INSURANCE,
        *LP,
        *MARKET,
        *TRAVELING,
        *PRODUCTION,
        *SKILL,
        *RENTAL,
    ],
    amount__lt=0,
)


class CorporationWalletQuerySet(models.QuerySet):
    def _convert_corp_tax(self, ess: models.QuerySet) -> Decimal:
        """Convert corp tax to correct amount for character ledger"""
        amount = (ess / app_settings.LEDGER_CORP_TAX) * (
            100 - app_settings.LEDGER_CORP_TAX
        )
        return amount

    def annotate_bounty_income(self) -> models.QuerySet:
        return self.annotate(
            bounty_income=Coalesce(
                Sum(
                    "amount",
                    filter=(BOUNTY_FILTER),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_ess_income(self, is_character: bool = False) -> models.QuerySet:
        if is_character:
            return self.annotate(
                ess_income=Round(
                    Coalesce(
                        Sum(
                            self._convert_corp_tax(F("amount")),
                            filter=(ESS_FILTER),
                        ),
                        Value(0),
                        output_field=DecimalField(),
                    ),
                    precision=2,
                )
            )
        return self.annotate(
            ess_income=Coalesce(
                Sum(
                    F("amount"),
                    filter=(ESS_FILTER),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    # pylint: disable=duplicate-code
    def annotate_miscellaneous(self) -> models.QuerySet:
        return self.annotate(
            miscellaneous=Coalesce(
                Sum(
                    "amount",
                    filter=(MISC_FILTER),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_costs(self) -> models.QuerySet:
        return self.annotate(
            costs=Coalesce(
                Sum(
                    "amount",
                    filter=Q(COSTS_FILTER) & Q(amount__lt=0),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )


class CorporationWalletManagerBase(models.Manager):
    pass


CorporationWalletManager = CorporationWalletManagerBase.from_queryset(
    CorporationWalletQuerySet
)


class CorporationDivisionQuerySet(models.QuerySet):
    pass


class CorporationDivisionManagerBase(models.Manager):
    pass


CorporationDivisionManager = CorporationDivisionManagerBase.from_queryset(
    CorporationDivisionQuerySet
)
