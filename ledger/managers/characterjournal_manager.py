from decimal import Decimal

from django.db import models
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce

from ledger import app_settings
from ledger.hooks import get_extension_logger, get_models_and_string
from ledger.view_helpers.core import events_filter

logger = get_extension_logger(__name__)
# PvE - Income
BOUNTY_PRIZES = ["bounty_prizes"]
MISSION_REWARD = ["agent_mission_reward", "agent_mission_time_bonus_reward"]
# Cost Ref Types
# pylint: disable=duplicate-code
CONTRACT_COST = [
    "contract_price_payment_corp",
    "contract_reward",
    "contract_price",
    "contract_collateral",
    "contract_reward_deposited",
]
MARKET_COST = ["market_escrow", "transaction_tax", "market_provider_tax", "brokers_fee"]
ASSETS_COST = ["asset_safety_recovery_tax"]
TRAVELING_COST = ["structure_gate_jump", "jump_clone_activation_fee"]
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
MARKET_TRADE = ["market_transaction"]
CONTRACT_TRADE = ["contract_price_payment_corp", "contract_reward", "contract_price"]
DONATION_TRADE = ["player_donation"]
INSURANCE_TRADE = ["insurance"]


class CharWalletQuerySet(models.QuerySet):
    # PvE - Income
    def annotate_bounty(self, character_ids: list, filter_date=None) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            ref_type__in=BOUNTY_PRIZES, second_party_id__in=character_ids
        )

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_bounty=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )

        return qs

    def annotate_ess(self, character_ids: list, filter_date=None) -> models.QuerySet:
        # pylint: disable=import-outside-toplevel
        from ledger.models.corporationaudit import CorporationWalletJournalEntry

        qs = CorporationWalletJournalEntry.objects.get_queryset()

        if filter_date:
            qs = qs.filter(filter_date)

        qs = events_filter(qs)

        return qs.annotate_ess(character_ids)

    def annotate_mission(
        self, character_ids: list, filter_date=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            second_party_id__in=character_ids, ref_type__in=MISSION_REWARD, amount__gt=0
        )

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_mission=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )

        return qs

    def annotate_mining(self, character_ids: list, filter_date=None) -> models.QuerySet:
        # pylint: disable=invalid-name
        CharacterMiningLedgerEntry, _ = get_models_and_string()

        qs = CharacterMiningLedgerEntry.objects.get_queryset()
        if app_settings.LEDGER_MEMBERAUDIT_USE:
            qs = qs.filter(character__eve_character__character_id__in=character_ids)
        else:
            qs = qs.filter(character__character__character_id__in=character_ids)

        if filter_date:
            qs = qs.filter(filter_date)

        if app_settings.LEDGER_MEMBERAUDIT_USE:
            qs = qs.annotate_pricing().values(
                "character__eve_character__character_id", "total"
            )
        else:
            qs = qs.annotate_pricing().values(
                "character__character__character_id", "total"
            )

        return qs

    # Costs
    def annotate_contract_cost(
        self, character_ids: list, filter_date=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids),
            ref_type__in=CONTRACT_COST,
            amount__lt=0,
        )

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_contract_cost=Coalesce(
                Sum("amount"), Value(0), output_field=DecimalField()
            )
        )

        return qs

    def annotate_market_cost(
        self, character_ids: list, filter_date=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids),
            ref_type__in=MARKET_COST,
            amount__lt=0,
        )

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_market_cost=Coalesce(
                Sum("amount"), Value(0), output_field=DecimalField()
            )
        )

        return qs

    def annotate_assets_cost(
        self, character_ids: list, filter_date=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids),
            ref_type__in=ASSETS_COST,
            amount__lt=0,
        )

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_assets_cost=Coalesce(
                Sum("amount"), Value(0), output_field=DecimalField()
            )
        )

        return qs

    def annotate_traveling_cost(
        self, character_ids: list, filter_date=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids),
            ref_type__in=TRAVELING_COST,
            amount__lt=0,
        )

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_traveling_cost=Coalesce(
                Sum("amount"), Value(0), output_field=DecimalField()
            )
        )

        return qs

    def annotate_production_cost(
        self, character_ids: list, filter_date=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids),
            ref_type__in=PRODUCTION_COST,
            amount__lt=0,
        )

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_production_cost=Coalesce(
                Sum("amount"), Value(0), output_field=DecimalField()
            )
        )

        return qs

    def annotate_skill_cost(
        self, character_ids: list, filter_date=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids),
            ref_type__in=SKILL_COST,
            amount__lt=0,
        )

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_skill_cost=Coalesce(
                Sum("amount"), Value(0), output_field=DecimalField()
            )
        )

        return qs

    def annotate_insurance_cost(
        self, character_ids: list, filter_date=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids),
            ref_type__in=INSURANCE_COST,
            amount__lt=0,
        )

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_insurance_cost=Coalesce(
                Sum("amount"), Value(0), output_field=DecimalField()
            )
        )

        return qs

    def annotate_planetary_cost(
        self, character_ids: list, filter_date=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids),
            ref_type__in=PLANETARY_COST,
            amount__lt=0,
        )

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_planetary_cost=Coalesce(
                Sum("amount"), Value(0), output_field=DecimalField()
            )
        )

        return qs

    def annotate_lp_cost(
        self, character_ids: list, filter_date=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids),
            ref_type__in=LP_COST,
            amount__lt=0,
        )

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_lp=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )

        return qs

    # Trading - Income
    def annotate_market_trade(
        self, character_ids: list, filter_date=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids),
            ref_type__in=MARKET_TRADE,
            amount__gt=0,
        )

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_market_trade=Coalesce(
                Sum("amount"), Value(0), output_field=DecimalField()
            )
        )

        return qs

    def annotate_contract_trade(
        self, character_ids: list, filter_date=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids),
            ref_type__in=CONTRACT_TRADE,
            amount__gt=0,
        )

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_contract_trade=Coalesce(
                Sum("amount"), Value(0), output_field=DecimalField()
            )
        )

        return qs

    def annotate_donation_trade(
        self, character_ids: list, filter_date=None, exclude=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids),
            ref_type__in=DONATION_TRADE,
            amount__gt=0,
        )

        if exclude:
            qs = qs.filter(~Q(first_party_id__in=exclude))

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_donation_trade=Coalesce(
                Sum("amount"), Value(0), output_field=DecimalField()
            )
        )

        return qs

    def annotate_insurance_trade(
        self, character_ids: list, filter_date=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        qs = CharacterWalletJournalEntry.objects.filter(
            second_party_id__in=character_ids,
            ref_type__in=INSURANCE_TRADE,
            amount__gt=0,
        )

        if filter_date:
            qs = qs.filter(filter_date)

        qs = qs.annotate(
            total_insurance_trade=Coalesce(
                Sum("amount"), Value(0), output_field=DecimalField()
            )
        )

        return qs

    def annotate_ledger(
        self, character_ids: list, filter_date=None, exclude=None
    ) -> models.QuerySet:
        # pylint: disable=invalid-name
        _, CharacterWalletJournalEntry = get_models_and_string()

        # Combine all filters
        qs = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids)
        )

        if filter_date:
            qs = qs.filter(filter_date)

        # Annotate all fields except ESS, Mining, and Donation Trade
        qs = qs.annotate(
            total_bounty=Coalesce(
                Sum("amount", filter=Q(ref_type__in=BOUNTY_PRIZES)),
                Value(0),
                output_field=DecimalField(),
            ),
            total_mission=Coalesce(
                Sum("amount", filter=Q(ref_type__in=MISSION_REWARD)),
                Value(0),
                output_field=DecimalField(),
            ),
            total_contract_cost=Coalesce(
                Sum("amount", filter=Q(ref_type__in=CONTRACT_COST, amount__lt=0)),
                Value(0),
                output_field=DecimalField(),
            ),
            total_market_cost=Coalesce(
                Sum("amount", filter=Q(ref_type__in=MARKET_COST, amount__lt=0)),
                Value(0),
                output_field=DecimalField(),
            ),
            total_assets_cost=Coalesce(
                Sum("amount", filter=Q(ref_type__in=ASSETS_COST, amount__lt=0)),
                Value(0),
                output_field=DecimalField(),
            ),
            total_traveling_cost=Coalesce(
                Sum("amount", filter=Q(ref_type__in=TRAVELING_COST, amount__lt=0)),
                Value(0),
                output_field=DecimalField(),
            ),
            total_production_cost=Coalesce(
                Sum("amount", filter=Q(ref_type__in=PRODUCTION_COST, amount__lt=0)),
                Value(0),
                output_field=DecimalField(),
            ),
            total_skill_cost=Coalesce(
                Sum("amount", filter=Q(ref_type__in=SKILL_COST, amount__lt=0)),
                Value(0),
                output_field=DecimalField(),
            ),
            total_insurance_cost=Coalesce(
                Sum("amount", filter=Q(ref_type__in=INSURANCE_COST, amount__lt=0)),
                Value(0),
                output_field=DecimalField(),
            ),
            total_planetary_cost=Coalesce(
                Sum("amount", filter=Q(ref_type__in=PLANETARY_COST, amount__lt=0)),
                Value(0),
                output_field=DecimalField(),
            ),
            total_lp=Coalesce(
                Sum("amount", filter=Q(ref_type__in=LP_COST, amount__lt=0)),
                Value(0),
                output_field=DecimalField(),
            ),
            total_market_trade=Coalesce(
                Sum("amount", filter=Q(ref_type__in=MARKET_TRADE, amount__gt=0)),
                Value(0),
                output_field=DecimalField(),
            ),
            total_contract_trade=Coalesce(
                Sum("amount", filter=Q(ref_type__in=CONTRACT_TRADE, amount__gt=0)),
                Value(0),
                output_field=DecimalField(),
            ),
            total_insurance_trade=Coalesce(
                Sum("amount", filter=Q(ref_type__in=INSURANCE_TRADE, amount__gt=0)),
                Value(0),
                output_field=DecimalField(),
            ),
        )

        # Aggregate the results directly from the original fields
        ledger_data = qs.aggregate(
            total_bounty=Sum("amount", filter=Q(ref_type__in=BOUNTY_PRIZES)),
            total_mission=Sum("amount", filter=Q(ref_type__in=MISSION_REWARD)),
            total_contract_cost=Sum(
                "amount", filter=Q(ref_type__in=CONTRACT_COST, amount__lt=0)
            ),
            total_market_cost=Sum(
                "amount", filter=Q(ref_type__in=MARKET_COST, amount__lt=0)
            ),
            total_assets_cost=Sum(
                "amount", filter=Q(ref_type__in=ASSETS_COST, amount__lt=0)
            ),
            total_traveling_cost=Sum(
                "amount", filter=Q(ref_type__in=TRAVELING_COST, amount__lt=0)
            ),
            total_production_cost=Sum(
                "amount", filter=Q(ref_type__in=PRODUCTION_COST, amount__lt=0)
            ),
            total_skill_cost=Sum(
                "amount", filter=Q(ref_type__in=SKILL_COST, amount__lt=0)
            ),
            total_insurance_cost=Sum(
                "amount", filter=Q(ref_type__in=INSURANCE_COST, amount__lt=0)
            ),
            total_planetary_cost=Sum(
                "amount", filter=Q(ref_type__in=PLANETARY_COST, amount__lt=0)
            ),
            total_lp=Sum("amount", filter=Q(ref_type__in=LP_COST, amount__lt=0)),
            total_market_trade=Sum(
                "amount", filter=Q(ref_type__in=MARKET_TRADE, amount__gt=0)
            ),
            total_contract_trade=Sum(
                "amount", filter=Q(ref_type__in=CONTRACT_TRADE, amount__gt=0)
            ),
            total_insurance_trade=Sum(
                "amount", filter=Q(ref_type__in=INSURANCE_TRADE, amount__gt=0)
            ),
        )

        # Special cases
        ess_data = self.annotate_ess(character_ids, filter_date).aggregate(
            total_ess=Sum("amount")
        )
        mining_data = self.annotate_mining(character_ids, filter_date).aggregate(
            total_mining=Sum("total")
        )
        donation_data = self.annotate_donation_trade(
            character_ids, filter_date, exclude
        ).aggregate(total_donation_trade=Sum("amount"))

        amounts = {
            "bounty": Decimal(ledger_data["total_bounty"] or 0),
            "ess": Decimal(ess_data["total_ess"] or 0),
            "mining": Decimal(mining_data["total_mining"] or 0),
        }

        amounts_others = {
            "mission": Decimal(ledger_data["total_mission"] or 0),
            "donation": Decimal(donation_data["total_donation_trade"] or 0),
            "transaction": Decimal(ledger_data["total_market_trade"] or 0),
            "contract": Decimal(ledger_data["total_contract_trade"] or 0),
            "insurance": Decimal(ledger_data["total_insurance_trade"] or 0),
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


class CharWalletManagerBase(models.Manager):
    def visible_to(self, user):
        return self.get_queryset().visible_to(user)


CharWalletManager = CharWalletManagerBase.from_queryset(
    CharWalletQuerySet
    if not app_settings.LEDGER_MEMBERAUDIT_USE
    else CharWalletQuerySet
)
