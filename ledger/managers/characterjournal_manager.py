from collections import defaultdict

from django.db import models
from django.db.models import (
    Case,
    DecimalField,
    ExpressionWrapper,
    F,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter

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
MILESTONE_REWARD = ["milestone_reward_payment"]
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
MILESTONE_REWARD_FILTER = Q(ref_type__in=MILESTONE_REWARD, amount__gt=0)
DAILY_GOAL_REWARD_FILTER = Q(ref_type__in=DAILY_GOAL_REWARD, amount__gt=0)

PVE_FILTER = BOUNTY_FILTER | ESS_FILTER
MISC_FILTER = (
    MARKET_INCOME_FILTER
    | CONTRACT_INCOME_FILTER
    | INSURANCE_INCOME_FILTER
    | MISSION_FILTER
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

    def annotate_ess(self, character_ids: list) -> models.QuerySet:
        # pylint: disable=import-outside-toplevel
        from ledger.models.corporationaudit import CorporationWalletJournalEntry

        return CorporationWalletJournalEntry.objects.annotate(
            total_ess=Coalesce(
                Sum(
                    "amount",
                    filter=Q(
                        ESS_FILTER,
                        second_party_id__in=character_ids,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_daily_goal(self, character_ids: list) -> models.QuerySet:
        # pylint: disable=import-outside-toplevel
        from ledger.models.corporationaudit import CorporationWalletJournalEntry

        return CorporationWalletJournalEntry.objects.annotate(
            total_daily_goal=Coalesce(
                Sum(
                    "amount",
                    Q(
                        DAILY_GOAL_REWARD_FILTER,
                        second_party_id__in=character_ids,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

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

    def annotate_mining(self, character_ids: list) -> models.QuerySet:
        # pylint: disable=import-outside-toplevel
        from ledger.models.characteraudit import CharacterMiningLedger

        return self.annotate(
            total_mining=Coalesce(
                Subquery(
                    CharacterMiningLedger.objects.filter(
                        character__character__character_id__in=character_ids
                    )
                    .annotate(
                        price=F("type__market_price__average_price"),
                        total=ExpressionWrapper(
                            F("type__market_price__average_price") * F("quantity"),
                            output_field=models.FloatField(),
                        ),
                    )
                    .values("character__character__character_id")
                    .annotate(total_amount=Sum("total"))
                    .values("total_amount")
                ),
                Value(0),
                output_field=DecimalField(),
            )
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

    def annotate_milestone_income(self, character_ids: list) -> models.QuerySet:
        return self.annotate(
            total_milestone_income=Coalesce(
                Sum(
                    "amount",
                    Q(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids),
                        MILESTONE_REWARD_FILTER,
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )


class CharWalletQuerySet(CharWalletQueryFilter):
    def _get_main_and_alts(self, character_ids: list) -> tuple[dict, set]:

        characters = {}
        char_list = []
        for char in character_ids:
            try:
                characters[char.character_id] = char
                char_list.append(char.character_id)
            except AttributeError:
                continue
        return characters, set(char_list)

    def generate_ledger(
        self, character_ids: list[EveCharacter], filter_date, exclude: list | None
    ):
        # pylint: disable=import-outside-toplevel
        from ledger.models.corporationaudit import CorporationWalletJournalEntry

        characters, char_list = self._get_main_and_alts(character_ids)

        qs = self.filter(
            Q(first_party_id__in=char_list) | Q(second_party_id__in=char_list)
        )

        qs = qs.filter(filter_date)

        # Subquery to identify entry_ids in total_contract_income
        contract_income_entry_ids = qs.filter(CONTRACT_INCOME_FILTER).values_list(
            "entry_id", flat=True
        )

        corporation_entry_ids = CorporationWalletJournalEntry.objects.filter(
            CONTRACT_COST_FILTER
        ).values_list("entry_id", flat=True)

        # Fiter Tax Events
        corporations_qs = CorporationWalletJournalEntry.objects.filter(
            ESS_FILTER,
            filter_date,
        )
        corporations_qs = events_filter(corporations_qs)

        characters = (
            qs.annotate(
                char_id=Case(
                    *[
                        When(
                            (Q(second_party_id=main_id) | (Q(first_party_id=main_id))),
                            then=Value(char.character_id),
                        )
                        for main_id, char in characters.items()
                    ],
                    output_field=models.IntegerField(),
                ),
                char_name=Case(
                    *[
                        When(
                            (Q(second_party_id=main_id) | (Q(first_party_id=main_id))),
                            then=Value(char.character_name),
                        )
                        for main_id, char in characters.items()
                    ],
                    output_field=models.CharField(),
                ),
            )
            .values("char_id", "char_name")
            .distinct()
        )

        qs = characters.annotate(
            total_bounty=Coalesce(
                Sum("amount", filter=BOUNTY_FILTER),
                Value(0),
                output_field=DecimalField(),
            ),
            total_ess=Coalesce(
                Subquery(
                    corporations_qs.filter(second_party_id=OuterRef("char_id"))
                    .values("second_party_id")
                    .annotate(total_amount=Sum("amount"))
                    .values("total_amount")
                ),
                Value(0),
                output_field=DecimalField(),
            ),
            total_others=Coalesce(
                Sum(
                    "amount",
                    filter=(
                        MISSION_FILTER
                        | INCURSION_FILTER
                        | LP_COST_FILTER
                        | DAILY_GOAL_REWARD_FILTER
                        | MARKET_INCOME_FILTER
                        | CONTRACT_INCOME_FILTER
                        & ~Q(entry_id__in=corporation_entry_ids)
                        | INSURANCE_INCOME_FILTER
                        | DONATION_INCOME_FILTER & ~Q(first_party_id__in=exclude)
                        if exclude
                        else DONATION_INCOME_FILTER | MILESTONE_REWARD_FILTER
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            ),
            total_costs=Coalesce(
                Sum(
                    "amount",
                    filter=(
                        CONTRACT_COST_FILTER
                        & ~Q(entry_id__in=contract_income_entry_ids)
                        | MARKET_COST_FILTER
                        | ASSETS_COST_FILTER
                        | TRAVELING_COST_FILTER
                        | PRODUCTION_COST_FILTER
                        | SKILL_COST_FILTER
                        | INSURANCE_COST_FILTER
                        | PLANETARY_COST_FILTER
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            ),
        )

        return qs

    def generate_template(
        self,
        amounts: defaultdict,
        character_ids: list,
        filter_date: timezone.datetime,
        exclude=None,
    ) -> dict:
        """Generate data template for the ledger character information view"""
        # pylint: disable=import-outside-toplevel
        from ledger.models.corporationaudit import CorporationWalletJournalEntry

        qs = self.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids)
        )

        # Subquery to identify entry_ids in contract filter
        contract_income_entry_ids = qs.filter(CONTRACT_INCOME_FILTER).values_list(
            "entry_id", flat=True
        )

        corporation_entry_ids = CorporationWalletJournalEntry.objects.filter(
            CONTRACT_COST_FILTER
        ).values_list("entry_id", flat=True)

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
            # Exclude Contract Income
            & ~Q(entry_id__in=contract_income_entry_ids),
            "traveling_cost": TRAVELING_COST_FILTER,
            "asset_cost": ASSETS_COST_FILTER,
            "skill_cost": SKILL_COST_FILTER,
            "insurance_cost": INSURANCE_COST_FILTER,
            "planetary_cost": PLANETARY_COST_FILTER,
            # Income
            "transaction": MARKET_INCOME_FILTER,
            "contract": CONTRACT_INCOME_FILTER
            # Exclude Corporation Contract Cost
            & ~Q(entry_id__in=corporation_entry_ids),
            "donation": (
                DONATION_INCOME_FILTER & ~Q(first_party_id__in=exclude)
                if exclude is not None
                else DONATION_INCOME_FILTER
            ),
            "milestone": MILESTONE_REWARD_FILTER,
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
