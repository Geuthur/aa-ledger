# Standard Library
import logging
from decimal import Decimal

# Django
from django.db.models import Q, QuerySet, Sum

# AA Ledger
from ledger import app_settings
from ledger.constants import (
    ASSETS,
    BOUNTY_PRIZES,
    CONTRACT,
    CORP_WITHDRAW,
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
    RENTAL,
    SKILL,
    TRAVELING,
)
from ledger.models.characteraudit import CharacterMiningLedger
from ledger.models.corporationaudit import (
    CorporationWalletJournalEntry,
)

logger = logging.getLogger(__name__)


def convert_corp_tax(amount: Decimal) -> Decimal:
    """Convert corp tax to correct amount for character ledger"""
    return (amount / app_settings.LEDGER_CORP_TAX) * (
        100 - app_settings.LEDGER_CORP_TAX
    )


class AggregateCore:
    def __init__(self, qs: QuerySet):
        self.queryset = qs


class AggegratePvE(AggregateCore):
    """Aggregate PvE class to process PvE data."""

    def aggregate_bounty(self, second_party=None):
        """Aggregate bounty data."""
        qs = self.queryset

        if isinstance(second_party, int):
            second_party = [second_party]

        if second_party:
            qs = qs.filter(second_party__in=second_party)

        return (
            qs.filter(Q(ref_type__in=BOUNTY_PRIZES) & Q(amount__gt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_ess(self, second_party=None, is_character=False):
        """Aggregate ESS data.
        This method is only for CorporationWalletJournalEntry.
        """
        qs = self.queryset

        if isinstance(second_party, int):
            second_party = [second_party]

        if second_party:
            qs = qs.filter(second_party__in=second_party)

        ess_amount = (
            qs.filter(Q(ref_type__in=ESS_TRANSFER) & Q(amount__gt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        if is_character:
            # Convert the ess amount to the correct value
            ess_amount = int(convert_corp_tax(ess_amount))

        return ess_amount

    def aggregate_mission(self, second_party=None):
        """Aggregate mission data."""
        qs = self.queryset

        if isinstance(second_party, int):
            second_party = [second_party]

        if second_party:
            qs = qs.filter(second_party__in=second_party)

        return (
            qs.filter(Q(ref_type__in=MISSION_REWARD) & Q(amount__gt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_incursion(self, second_party=None):
        """Aggregate incursion data."""
        qs = self.queryset

        if isinstance(second_party, int):
            second_party = [second_party]

        if second_party:
            qs = qs.filter(second_party__in=second_party)

        return (
            qs.filter(Q(ref_type__in=INCURSION) & Q(amount__gt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )


class AggregateMining(AggregateCore):
    """Aggregate Mining class to process mining data."""

    def aggregate_mining(self, characters=None):
        """Aggregate mining data."""
        if self.queryset.model != CharacterMiningLedger:
            raise TypeError("This method is only for CharacterMiningLedger")
        qs = self.queryset

        if isinstance(characters, int):
            characters = [characters]

        if characters:
            qs = qs.filter(character__character__character_id__in=characters)

        qs = qs.annotate_mining()

        if qs:
            return int(qs[0]["total_amount"])
        return 0


class AggregateCosts(AggregateCore):

    def aggregate_market_cost(self, first_party=None):
        """Aggregate market cost data."""
        qs = self.queryset

        if isinstance(first_party, int):
            first_party = [first_party]

        if first_party:
            # Filter Costs
            qs = qs.filter(first_party__in=first_party)

        return (
            qs.filter(Q(ref_type__in=MARKET) & Q(amount__lt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_insurance_cost(self, first_party=None):
        """Aggregate insurance cost data."""
        qs = self.queryset

        if isinstance(first_party, int):
            first_party = [first_party]

        if first_party:
            # Filter Costs
            qs = qs.filter(first_party__in=first_party)

        return (
            qs.filter(Q(ref_type__in=INSURANCE) & Q(amount__lt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_contract_cost(self, first_party=None):
        """Aggregate contract data."""
        qs = self.queryset

        if isinstance(first_party, int):
            first_party = [first_party]

        if first_party:
            # Filter Costs
            qs = qs.filter(first_party__in=first_party)

        return (
            qs.filter(Q(ref_type__in=CONTRACT) & Q(amount__lt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_lp_cost(self, first_party=None):
        """Aggregate LP cost data."""
        qs = self.queryset

        if isinstance(first_party, int):
            first_party = [first_party]

        if first_party:
            # Filter Costs
            qs = qs.filter(first_party__in=first_party)

        return (
            qs.filter(Q(ref_type__in=LP) & Q(amount__lt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_production_cost(self, first_party=None):
        """Aggregate production cost data."""
        qs = self.queryset

        if isinstance(first_party, int):
            first_party = [first_party]

        if first_party:
            # Filter Costs
            qs = qs.filter(first_party__in=first_party)

        return (
            qs.filter(Q(ref_type__in=PRODUCTION) & Q(amount__lt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_costs(self, first_party=None):
        """Aggregate costs data."""
        qs = self.queryset

        if isinstance(first_party, int):
            first_party = [first_party]

        if first_party:
            # Filter Costs
            qs = qs.filter(first_party__in=first_party)

        return (
            qs.filter(
                Q(
                    ref_type__in=[
                        *MARKET,
                        *CONTRACT,
                        *TRAVELING,
                        *PRODUCTION,
                        *ASSETS,
                        *SKILL,
                        *PLANETARY,
                        *LP,
                        *INSURANCE,
                        *RENTAL,
                    ]
                )
                & Q(amount__lt=0)
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )


class AggregateCorporation(AggregateCore):
    """Aggregate Corporation class to process corporation data."""

    def aggregate_daily_goal(self, second_party=None, is_character=False):
        """
        Aggregate daily goal data.
        This method is only for CorporationWalletJournalEntry.
        """
        if self.queryset.model != CorporationWalletJournalEntry:
            raise TypeError("This method is only for CorporationWalletJournalEntry")

        qs = self.queryset

        if isinstance(second_party, int):
            second_party = [second_party]

        if second_party:
            qs = qs.filter(second_party__in=second_party)

        daily_goal = (
            qs.filter(Q(ref_type__in=DAILY_GOAL_REWARD, amount__gt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        if is_character:
            # Convert the ess amount to the correct value
            daily_goal = int(convert_corp_tax(daily_goal))

        return daily_goal

    def aggregate_corp_withdraw(self, first_party=None, exclude=None):
        """Aggregate corp withdraw cost data."""
        qs = self.queryset

        if isinstance(first_party, int):
            first_party = [first_party]

        if first_party:
            # Filter Costs
            qs = qs.filter(first_party__in=first_party)

        if isinstance(exclude, int):
            exclude = [exclude]

        if exclude:
            qs = qs.exclude(second_party_id__in=exclude)

        return (
            qs.filter(Q(ref_type__in=CORP_WITHDRAW) & Q(amount__gt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_corp_withdraw_cost(self, first_party=None, exclude=None):
        """Aggregate corp withdraw cost data."""
        qs = self.queryset

        if isinstance(first_party, int):
            first_party = [first_party]

        if first_party:
            # Filter Costs
            qs = qs.filter(first_party__in=first_party)

        if isinstance(exclude, int):
            exclude = [exclude]

        if exclude:
            qs = qs.exclude(second_party_id__in=exclude)

        return (
            qs.filter(Q(ref_type__in=CORP_WITHDRAW) & Q(amount__lt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )


class AggregateLedger(
    AggegratePvE, AggregateCosts, AggregateCorporation, AggregateCore
):
    """Aggregate Ledger class to process ledger data."""

    def aggregate_insurance(self, second_party=None):
        """Aggregate insurance data."""
        qs = self.queryset

        if isinstance(second_party, int):
            second_party = [second_party]

        if second_party:
            # Filter Insurance
            qs = qs.filter(second_party__in=second_party)

        return (
            qs.filter(Q(ref_type__in=INSURANCE) & Q(amount__gt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_market(self, second_party=None):
        """Aggregate market data."""
        qs = self.queryset

        if isinstance(second_party, int):
            second_party = [second_party]

        if second_party:
            # Filter Market
            qs = qs.filter(second_party__in=second_party)

        return (
            qs.filter(Q(ref_type__in=MARKET) & Q(amount__gt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_contract(self, second_party=None):
        """Aggregate contract data."""
        qs = self.queryset

        if isinstance(second_party, int):
            second_party = [second_party]

        if second_party:
            # Filter Contract
            qs = qs.filter(second_party__in=second_party)

        return (
            qs.filter(Q(ref_type__in=CONTRACT) & Q(amount__gt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_donation(self, second_party=None, exclude=None):
        """Aggregate donation data optional with exclude."""
        qs = self.queryset

        if isinstance(second_party, int):
            second_party = [second_party]

        if isinstance(exclude, int):
            exclude = [exclude]

        if exclude:
            qs = qs.exclude(first_party_id__in=exclude)

        if second_party:
            qs = qs.filter(second_party__in=second_party)

        return (
            qs.filter(Q(ref_type__in=DONATION, amount__gt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_milestone_reward(self, second_party=None):
        """Aggregate milestone reward data."""
        qs = self.queryset

        if isinstance(second_party, int):
            second_party = [second_party]

        if second_party:
            qs = qs.filter(second_party__in=second_party)

        return (
            qs.filter(Q(ref_type__in=MILESTONE_REWARD, amount__gt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_production(self, first_party=None):
        """Aggregate production data."""
        qs = self.queryset

        if isinstance(first_party, int):
            first_party = [first_party]

        if first_party:
            # Filter Costs
            qs = qs.filter(first_party__in=first_party)

        return (
            qs.filter(Q(ref_type__in=PRODUCTION) & Q(amount__gt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_traveling(self, first_party=None):
        """Aggregate traveling data."""
        qs = self.queryset

        if isinstance(first_party, int):
            first_party = [first_party]

        if first_party:
            # Filter Costs
            qs = qs.filter(first_party__in=first_party)

        return (
            qs.filter(Q(ref_type__in=TRAVELING)).aggregate(total=Sum("amount"))["total"]
            or 0
        )

    def aggregate_assets(self, first_party=None):
        """Aggregate assets cost data."""
        qs = self.queryset

        if isinstance(first_party, int):
            first_party = [first_party]

        if first_party:
            # Filter Costs
            qs = qs.filter(first_party__in=first_party)

        return (
            qs.filter(Q(ref_type__in=ASSETS) & Q(amount__lt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_skill(self, first_party=None):
        """Aggregate skill cost data."""
        qs = self.queryset

        if isinstance(first_party, int):
            first_party = [first_party]

        if first_party:
            # Filter Costs
            qs = qs.filter(first_party__in=first_party)

        return (
            qs.filter(Q(ref_type__in=SKILL) & Q(amount__lt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_planetary(self, first_party=None):
        """Aggregate planetary cost data."""
        qs = self.queryset

        if isinstance(first_party, int):
            first_party = [first_party]

        if first_party:
            # Filter Costs
            qs = qs.filter(first_party__in=first_party)

        return (
            qs.filter(Q(ref_type__in=PLANETARY) & Q(amount__lt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_rental(self, first_party=None):
        """Aggregate rental cost data."""
        qs = self.queryset

        if isinstance(first_party, int):
            first_party = [first_party]

        if first_party:
            # Filter Costs
            qs = qs.filter(first_party__in=first_party)

        return (
            qs.filter(Q(ref_type__in=RENTAL) & Q(amount__lt=0)).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

    def aggregate_miscellaneous(self, second_party=None):
        """Aggregate miscellaneous data."""
        qs = self.queryset

        if isinstance(second_party, int):
            second_party = [second_party]

        if second_party:
            # Filter Income
            qs = qs.filter(second_party__in=second_party)

        return (
            qs.filter(
                Q(
                    ref_type__in=[
                        *ASSETS,
                        *CONTRACT,
                        *DAILY_GOAL_REWARD,
                        *INCURSION,
                        *INSURANCE,
                        *MISSION_REWARD,
                        *MARKET,
                        *PRODUCTION,
                        *TRAVELING,
                        *SKILL,
                        *PLANETARY,
                        *LP,
                    ]
                )
                & Q(amount__gt=0)
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
