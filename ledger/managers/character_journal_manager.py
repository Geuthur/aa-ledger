# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.decorators import log_timing
from ledger.helpers.etag import (
    etag_results,
)
from ledger.helpers.ref_type import RefTypeManager
from ledger.providers import esi

if TYPE_CHECKING:
    # AA Ledger
    from ledger.models.characteraudit import (
        CharacterAudit,
    )
    from ledger.models.general import UpdateSectionResult

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CharWalletIncomeFilter(models.QuerySet):
    # PvE - Income
    def annotate_bounty_income(self) -> models.QuerySet:
        return self.annotate(
            bounty_income=Coalesce(
                Sum(
                    "amount",
                    filter=Q(ref_type__in=RefTypeManager.BOUNTY_PRIZES, amount__gt=0),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_ess_income(self) -> models.QuerySet:
        return self.annotate(
            ess_income=Coalesce(
                Sum(
                    "amount",
                    filter=Q(ref_type__in=RefTypeManager.ESS_TRANSFER, amount__gt=0),
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
                    filter=Q(ref_type__in=RefTypeManager.MISSION_REWARD, amount__gt=0),
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
                    filter=Q(ref_type__in=RefTypeManager.INCURSION, amount__gt=0),
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
                    filter=Q(ref_type__in=RefTypeManager.MARKET, amount__gt=0),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_contract_income(self) -> models.QuerySet:
        contract_types = list(RefTypeManager.CONTRACT) + list(
            RefTypeManager.CORPORATION_CONTRACT
        )
        return self.annotate(
            contract_income=Coalesce(
                Sum(
                    "amount",
                    filter=Q(ref_type__in=contract_types, amount__gt=0),
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
                    filter=Q(ref_type__in=RefTypeManager.DONATION, amount__gt=0)
                    & ~Q(first_party_id__in=exclude),
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
                    filter=Q(ref_type__in=RefTypeManager.INSURANCE, amount__gt=0),
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
                    filter=Q(
                        ref_type__in=RefTypeManager.MILESTONE_REWARD, amount__gt=0
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_daily_goal_income(self) -> models.QuerySet:
        """Annotate daily goal income."""
        return self.annotate(
            daily_goal_income=Coalesce(
                Sum(
                    "amount",
                    filter=Q(
                        ref_type__in=RefTypeManager.DAILY_GOAL_REWARD, amount__gt=0
                    ),
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
                    filter=Q(ref_type__in=RefTypeManager.all_ref_types(), amount__gt=0),
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
                    filter=Q(ref_type__in=RefTypeManager.all_ref_types(), amount__lt=0),
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
                    filter=Q(ref_type__in=RefTypeManager.CONTRACT, amount__lt=0),
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
                    filter=Q(ref_type__in=RefTypeManager.MARKET, amount__lt=0),
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
                    filter=Q(ref_type__in=RefTypeManager.ASSETS, amount__lt=0),
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
                    filter=Q(ref_type__in=RefTypeManager.TRAVELING, amount__lt=0),
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
                    filter=Q(ref_type__in=RefTypeManager.PRODUCTION, amount__lt=0),
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
                    filter=Q(ref_type__in=RefTypeManager.SKILL, amount__lt=0),
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
                    filter=Q(ref_type__in=RefTypeManager.INSURANCE, amount__lt=0),
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
                    filter=Q(ref_type__in=RefTypeManager.PLANETARY, amount__lt=0),
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
                    filter=Q(ref_type__in=RefTypeManager.LP, amount__lt=0),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )


# pylint: disable=used-before-assignment
class CharWalletQuerySet(CharWalletCostQueryFilter):
    @log_timing(logger)
    def update_or_create_esi(
        self, character: "CharacterAudit", force_refresh: bool = False
    ) -> "UpdateSectionResult":
        """Update or Create a wallet journal entry from ESI data."""
        return character.update_section_if_changed(
            section=character.UpdateSection.WALLET_JOURNAL,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(
        self, character: "CharacterAudit", force_refresh: bool = False
    ) -> None:
        """Fetch wallet journal entries from ESI data."""
        req_scopes = ["esi-wallet.read_character_wallet.v1"]

        token = character.get_token(scopes=req_scopes)
        journal_items_ob = esi.client.Wallet.get_characters_character_id_wallet_journal(
            character_id=character.eve_character.character_id
        )
        journal_items = etag_results(
            journal_items_ob, token, force_refresh=force_refresh
        )
        self._update_or_create_objs(character, journal_items)

    @transaction.atomic()
    def _update_or_create_objs(self, character: "CharacterAudit", objs: list) -> None:
        """Update or Create wallet journal entries from objs data."""
        # pylint: disable=import-outside-toplevel
        # AA Ledger
        from ledger.models.general import EveEntity

        _current_journal = self.filter(character=character).values_list(
            "entry_id", flat=True
        )  # TODO add time filter
        _current_eve_ids = list(
            EveEntity.objects.all().values_list("eve_id", flat=True)
        )

        _new_names = []

        items = []
        for item in objs:
            if item.get("id") not in _current_journal:
                if item.get("second_party_id") not in _current_eve_ids:
                    _new_names.append(item.get("second_party_id"))
                    _current_eve_ids.append(item.get("second_party_id"))
                if item.get("first_party_id") not in _current_eve_ids:
                    _new_names.append(item.get("first_party_id"))
                    _current_eve_ids.append(item.get("first_party_id"))

                # pylint: disable=duplicate-code
                asset_item = self.model(
                    character=character,
                    amount=item.get("amount"),
                    balance=item.get("balance"),
                    context_id=item.get("context_id"),
                    context_id_type=item.get("context_id_type"),
                    date=item.get("date"),
                    description=item.get("description"),
                    first_party_id=item.get("first_party_id"),
                    entry_id=item.get("id"),
                    reason=item.get("reason"),
                    ref_type=item.get("ref_type"),
                    second_party_id=item.get("second_party_id"),
                    tax=item.get("tax"),
                    tax_receiver_id=item.get("tax_receiver_id"),
                )
                items.append(asset_item)

        created_names = EveEntity.objects.create_bulk_from_esi(_new_names)

        if created_names:
            self.bulk_create(items)
        else:
            raise TokenError("ESI Fail")

    def aggregate_bounty(self) -> dict:
        """Aggregate bounty income."""
        return self.filter(ref_type__in=RefTypeManager.BOUNTY_PRIZES).aggregate(
            total_bounty=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )["total_bounty"]

    def aggregate_ess(self) -> dict:
        """Aggregate ESS income."""
        return self.filter(ref_type__in=RefTypeManager.ESS_TRANSFER).aggregate(
            total_ess=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )["total_ess"]

    def aggregate_costs(self, first_party=None, second_party=None) -> dict:
        """Aggregate costs. first_party wird für donation exkludiert."""
        qs = self
        cost_types = RefTypeManager.all_ref_types()
        donation_types = RefTypeManager.DONATION

        if first_party is not None:
            if isinstance(first_party, int):
                first_party = [first_party]
            qs = qs.filter(first_party__in=first_party)

        if second_party is not None:
            if isinstance(second_party, int):
                second_party = [second_party]
            # Exclude: alle donation mit first_party_id in Liste, Rest wie gehabt
            qs = qs.exclude(
                Q(ref_type__in=donation_types, first_party_id__in=second_party)
            )
            qs = qs.filter(Q(ref_type__in=cost_types))
        else:
            qs = qs.filter(Q(ref_type__in=cost_types))

        qs = qs.filter(amount__lt=0)
        return qs.aggregate(
            total_costs=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )["total_costs"]

    def aggregate_miscellaneous(self, first_party=None, second_party=None) -> dict:
        """Aggregate miscellaneous income. first_party wird nur für donation angewandt."""
        qs = self

        misc_types = RefTypeManager.all_ref_types()
        donation_types = RefTypeManager.DONATION

        if first_party is not None:
            if isinstance(first_party, int):
                first_party = [first_party]
            # Exclude: alle donation mit first_party_id in Liste, Rest wie gehabt
            qs = qs.exclude(
                Q(ref_type__in=donation_types, first_party_id__in=first_party)
            )
            qs = qs.filter(Q(ref_type__in=misc_types))
        else:
            qs = qs.filter(Q(ref_type__in=misc_types))

        if second_party is not None:
            if isinstance(second_party, int):
                second_party = [second_party]
            qs = qs.filter(second_party__in=second_party)

        qs = qs.filter(amount__gt=0)
        return qs.aggregate(
            total_misc=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )["total_misc"]

    # pylint: disable=too-many-positional-arguments
    def aggregate_ref_type(
        self,
        ref_type: list,
        first_party=None,
        second_party=None,
        exclude=None,
        income: bool = False,
    ) -> dict:
        """Aggregate income by ref_type."""
        qs = self.filter(ref_type__in=ref_type)

        if first_party is not None:
            if isinstance(first_party, int):
                first_party = [first_party]
            qs = qs.filter(first_party__in=first_party)

        if second_party is not None:
            if isinstance(second_party, int):
                second_party = [second_party]
            qs = qs.filter(second_party__in=second_party)

        if exclude is not None:
            if isinstance(exclude, int):
                exclude = [exclude]
            qs = qs.exclude(first_party__in=exclude)

        if income:
            qs = qs.filter(amount__gt=0)
        else:
            qs = qs.filter(amount__lt=0)

        return qs.aggregate(
            total=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )["total"]


class CharWalletManagerBase(models.Manager):
    pass


CharWalletManager = CharWalletManagerBase.from_queryset(CharWalletQuerySet)
