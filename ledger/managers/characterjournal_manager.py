from collections import defaultdict

from django.db import models
from django.db.models import (
    Case,
    DecimalField,
    ExpressionWrapper,
    F,
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
DAILY_GOAL_REWARD_FILTER = Q(ref_type__in=DAILY_GOAL_REWARD, amount__gt=0)
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

PVE_FILTER = BOUNTY_FILTER | ESS_FILTER
MISC_FILTER = (
    MARKET_INCOME_FILTER
    | INSURANCE_INCOME_FILTER
    | MISSION_FILTER
    | INCURSION_FILTER
    | MILESTONE_REWARD_FILTER
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


class CharWalletIncomeFilter(models.QuerySet):
    # PvE - Income
    def annotate_bounty(self) -> models.QuerySet:
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
        # pylint: disable=import-outside-toplevel
        from ledger.models.corporationaudit import CorporationWalletJournalEntry

        # Check all Contracts from Corporations Member and Exclude them from be calculated
        corporation_entry_ids = CorporationWalletJournalEntry.objects.filter(
            CONTRACT_COST_FILTER
        ).values_list("entry_id", flat=True)

        contract_income_filter = CONTRACT_INCOME_FILTER & ~Q(
            entry_id__in=corporation_entry_ids
        )
        return self.annotate(
            contract_income=Coalesce(
                Sum(
                    "amount",
                    filter=contract_income_filter,
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_donation_income(self, exclude=None) -> models.QuerySet:
        qs = self

        exclude_filter = DONATION_INCOME_FILTER
        if exclude:
            exclude_filter &= ~Q(first_party_id__in=exclude)

        return qs.annotate(
            donation_income=Coalesce(
                Sum(
                    "amount",
                    filter=exclude_filter,
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
    def annotate_ess(self, character_ids: list) -> models.QuerySet:
        # pylint: disable=import-outside-toplevel
        from ledger.models.corporationaudit import CorporationWalletJournalEntry

        return CorporationWalletJournalEntry.objects.annotate(
            ess=Coalesce(
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

    def annotate_mining(self, character_ids: list) -> models.QuerySet:
        # pylint: disable=import-outside-toplevel
        from ledger.models.characteraudit import CharacterMiningLedger

        return self.annotate(
            mining=Coalesce(
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
        # Subquery to identify entry_ids that are contract income
        contract_income_entry_ids = self.filter(CONTRACT_INCOME_FILTER).values_list(
            "entry_id", flat=True
        )
        contract_cost_filter = CONTRACT_COST_FILTER & ~Q(
            entry_id__in=contract_income_entry_ids
        )

        return self.annotate(
            contract_cost=Coalesce(
                Sum(
                    "amount",
                    filter=contract_cost_filter,
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
    def _get_main_and_alts(self, characters: list[EveCharacter]) -> tuple[dict, set]:
        characters_dict = {}
        char_list = []
        for char in characters:
            try:
                characters_dict[char.character_id] = char
                char_list.append(char.character_id)
            except AttributeError:
                continue
        return characters_dict, set(char_list)

    def _get_models_qs(
        self, character_ids: list, filter_date: Q
    ) -> tuple[models.QuerySet, models.QuerySet]:
        """Get the models queryset for the character ledger"""
        # pylint: disable=import-outside-toplevel
        from ledger.models.characteraudit import CharacterMiningLedger
        from ledger.models.corporationaudit import CorporationWalletJournalEntry

        # Call annotate_ledger and store the result
        char_mining_journal = CharacterMiningLedger.objects.filter(
            Q(character__character__character_id__in=character_ids) & Q(filter_date)
        )

        corp_character_journal = CorporationWalletJournalEntry.objects.filter(
            Q(second_party_id__in=character_ids) & Q(filter_date)
        )
        return char_mining_journal, corp_character_journal

    def get_ledger_data(self, queryset, exclude: list | None) -> models.QuerySet:
        """Get the ledger data"""
        return (
            queryset
            # PvE
            .annotate_bounty()
            # Income
            .annotate_mission_income()
            .annotate_incursion_income()
            .annotate_insurance_income()
            .annotate_market_income()
            .annotate_contract_income()
            .annotate_donation_income(exclude=exclude)
            .annotate_milestone_income()
            # Costs
            .annotate_market_cost()
            .annotate_production_cost()
            .annotate_contract_cost()
            .annotate_lp_cost()
            .annotate_traveling_cost()
            .annotate_asset_cost()
            .annotate_skill_cost()
            .annotate_insurance_cost()
            .annotate_planetary_cost()
        )

    def generate_ledger(
        self, characters: list[EveCharacter], filter_date, exclude: list | None
    ) -> tuple[models.QuerySet, models.QuerySet, models.QuerySet]:
        characters, char_list = self._get_main_and_alts(characters)

        qs = self.filter(
            Q(first_party_id__in=char_list) | Q(second_party_id__in=char_list)
        )

        qs = qs.filter(filter_date)

        mining_qs, corp_qs = self._get_models_qs(char_list, filter_date)

        # Fiter Tax Events
        corp_qs = events_filter(corp_qs)

        characters = qs.annotate(
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
        ).values("char_id", "char_name")

        # Annotate All Ledger Data
        characters = self.get_ledger_data(characters, exclude)

        char_qs = characters.annotate(
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
            ),
            costs=Coalesce(
                F("market_cost")
                + F("production_cost")
                + F("contract_cost")
                + F("lp_cost")
                + F("traveling_cost")
                + F("asset_cost")
                + F("skill_cost")
                + F("insurance_cost")
                + F("planetary_cost"),
                Value(0),
                output_field=DecimalField(),
            ),
        )
        return char_qs, mining_qs, corp_qs

    def generate_template(
        self,
        amounts: defaultdict,
        character_ids: list,
        filter_date: timezone.datetime,
        exclude=None,
    ) -> dict:
        """Generate data template for the ledger character information view"""
        # Define the types and their respective filters
        type_names = [
            # PvE
            "bounty_income",
            # Costs
            "market_cost",
            "production_cost",
            "contract_cost",
            "lp_cost",
            "traveling_cost",
            "asset_cost",
            "skill_cost",
            "insurance_cost",
            "planetary_cost",
            # Income
            "mission_income",
            "incursion_income",
            "insurance_income",
            "market_income",
            "contract_income",
            "donation_income",
            "milestone_income",
        ]

        qs = self.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids)
        )

        qs = self.get_ledger_data(qs, exclude)

        annotations = {}
        for type_name in type_names:
            annotations[f"{type_name}_total_amount"] = Coalesce(
                Sum(
                    Case(
                        When(
                            **{
                                f"{type_name}__isnull": False,
                                "date__year": filter_date.year,
                            },
                            then=F(type_name),
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
                            **{
                                f"{type_name}__isnull": False,
                                "date__year": filter_date.year,
                                "date__month": filter_date.month,
                                "date__day": filter_date.day,
                            },
                            then=F(type_name),
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
                            **{
                                f"{type_name}__isnull": False,
                                "date__year": filter_date.year,
                                "date__month": filter_date.month,
                                "date__day": filter_date.day,
                                "date__hour": filter_date.hour,
                            },
                            then=F(type_name),
                        )
                    )
                ),
                Value(0),
                output_field=DecimalField(),
            )

        qs = qs.aggregate(**annotations)

        for type_name in type_names:
            amounts[type_name]["total_amount"] = qs[f"{type_name}_total_amount"]
            amounts[type_name]["total_amount_day"] = qs[f"{type_name}_total_amount_day"]
            amounts[type_name]["total_amount_hour"] = qs[
                f"{type_name}_total_amount_hour"
            ]

        return amounts

    def annotate_billboard(self, chars: list, exclude: list) -> models.QuerySet:
        qs = self.filter(Q(first_party_id__in=chars) | Q(second_party_id__in=chars))
        qs = self.get_ledger_data(qs, exclude)
        qs = qs.annotate(
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
            ),
            costs=Coalesce(
                F("market_cost")
                + F("production_cost")
                + F("contract_cost")
                + F("lp_cost")
                + F("traveling_cost")
                + F("asset_cost")
                + F("skill_cost")
                + F("insurance_cost")
                + F("planetary_cost"),
                Value(0),
                output_field=DecimalField(),
            ),
        )
        return qs


class CharWalletManagerBase(models.Manager):
    pass


CharWalletManager = CharWalletManagerBase.from_queryset(CharWalletQuerySet)
