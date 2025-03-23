import json
import logging
from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Case, DecimalField, F, Q, Sum, Value, When
from django.db.models.functions import Coalesce, Round
from django.utils import timezone

from allianceauth.authentication.models import UserProfile

from ledger import app_settings
from ledger.managers.manager_helper import _annotations_information
from ledger.models.general import EveEntity
from ledger.view_helpers.core import events_filter

logger = logging.getLogger(__name__)

# Ref Types PvE - Tax Income
BOUNTY_PRIZES = ["bounty_prizes"]
ESS_TRANSFER = ["ess_escrow_transfer"]
INCURSION = ["corporate_reward_payout"]
MISSION = ["agent_mission_reward", "agent_mission_time_bonus_reward"]
DAILY_GOAL_REWARD = ["daily_goal_payouts"]
CITADEL_INCOME = ["industry_job_tax", "reprocessing_tax"]

# Filters
BOUNTY_FILTER = Q(ref_type__in=BOUNTY_PRIZES, amount__gt=0)
ESS_FILTER = Q(ref_type__in=ESS_TRANSFER, amount__gt=0)
INCURSION_FILTER = Q(ref_type__in=INCURSION, amount__gt=0)
MISSION_FILTER = Q(ref_type__in=MISSION, amount__gt=0)
DAILY_GOAL_REWARD_FILTER = Q(ref_type__in=DAILY_GOAL_REWARD, amount__gt=0)
CITADEL_FILTER = Q(ref_type__in=CITADEL_INCOME, amount__gt=0)

MISC_FILTER = (
    INCURSION_FILTER | MISSION_FILTER | DAILY_GOAL_REWARD_FILTER | CITADEL_FILTER
)


class CorpWalletQueryFilter(models.QuerySet):
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

    def annotate_ess_income(self, is_character_ledger: bool = False) -> models.QuerySet:
        if is_character_ledger:
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
    def annotate_mission_income(self) -> models.QuerySet:
        return self.annotate(
            mission_income=Coalesce(
                Sum(
                    "amount",
                    filter=(MISSION_FILTER),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    # pylint: disable=duplicate-code
    def annotate_incursion_income(self) -> models.QuerySet:
        return self.annotate(
            incursion_income=Coalesce(
                Sum(
                    "amount",
                    filter=(INCURSION_FILTER),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_daily_goal_income(
        self, is_character_ledger: bool = False
    ) -> models.QuerySet:
        if is_character_ledger:
            return self.annotate(
                daily_goal_income=Round(
                    Coalesce(
                        Sum(
                            self._convert_corp_tax(F("amount")),
                            filter=(DAILY_GOAL_REWARD_FILTER),
                        ),
                        Value(0),
                        output_field=DecimalField(),
                    ),
                    precision=2,
                )
            )
        return self.annotate(
            daily_goal_income=Coalesce(
                Sum(
                    F("amount"),
                    filter=(DAILY_GOAL_REWARD_FILTER),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_citadel_income(self) -> models.QuerySet:
        return self.annotate(
            citadel_income=Coalesce(
                Sum(
                    "amount",
                    filter=(CITADEL_FILTER),
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


class CorpWalletQuerySet(CorpWalletQueryFilter):
    def _get_linked_chars(self, entity_ids: list) -> tuple:
        main_and_alts = {}
        entity_list = []

        accounts = UserProfile.objects.filter(
            main_character__isnull=False,
        ).select_related(
            "user__profile__main_character",
            "main_character__character_ownership",
            "main_character__character_ownership__user__profile",
            "main_character__character_ownership__user__profile__main_character",
        )

        for account in accounts:
            alts = account.user.character_ownerships.all().values_list(
                "character__character_id", flat=True
            )

            main = account.main_character

            try:
                main_char = EveEntity.objects.get(eve_id=main.character_id)
            except ObjectDoesNotExist:
                main_char = EveEntity(
                    eve_id=main.character_id,
                    name=main.character_name,
                    category="character",
                )

            main_and_alts[main_char.eve_id] = {
                "main_id": main_char.eve_id,
                "name": main_char.name,
                "alts": list(alts),
                "entity_type": "character",
            }
            entity_list.extend(alts)

        missing_entitys = set(entity_ids) - set(entity_list)
        entity_list.extend(missing_entitys)

        return main_and_alts, set(entity_list)

    def _annotate_main_and_alts(
        self, qs: models.QuerySet, main_and_alts: dict, entity_ids: list
    ) -> models.QuerySet:
        """Annotate the queryset with main and alts"""
        # Create annotation cases
        main_entity_id_cases = []
        main_entity_name_cases = []
        main_entity_type_cases = []
        alts_cases = []

        for main, data in main_and_alts.items():
            # Filter entitys to include only those alt that are present in entity_ids
            f_entity_ids = list(set(data["alts"]) & entity_ids)

            if f_entity_ids:
                main_entity_id_cases.append(
                    When(
                        Q(second_party_id__in=f_entity_ids)
                        | Q(first_party_id__in=f_entity_ids),
                        then=Value(main),
                    )
                )
                main_entity_name_cases.append(
                    When(
                        Q(second_party_id__in=f_entity_ids)
                        | Q(first_party_id__in=f_entity_ids),
                        then=Value(data["name"]),
                    )
                )
                main_entity_type_cases.append(
                    When(
                        Q(second_party_id__in=f_entity_ids)
                        | Q(first_party_id__in=f_entity_ids),
                        then=Value(data["entity_type"]),
                    )
                )
                alts_cases.append(
                    When(
                        Q(second_party_id__in=f_entity_ids)
                        | Q(first_party_id__in=f_entity_ids),
                        then=Value(json.dumps(f_entity_ids)),
                    )
                )

        # Annotate the queryset
        qs = qs.annotate(
            main_entity_id=Case(
                *main_entity_id_cases,
                output_field=models.IntegerField(),
            ),
            main_entity_name=Case(
                *main_entity_name_cases,
                output_field=models.CharField(),
            ),
            main_entity_type=Case(
                *main_entity_type_cases,
                output_field=models.CharField(),
            ),
            alts=Case(
                *alts_cases,
                default=Value("[]"),
                output_field=models.JSONField(),
            ),
        ).values(
            "main_entity_id",
            "main_entity_name",
            "main_entity_type",
            "alts",
        )
        return qs

    def annotate_ledger_data(self, queryset) -> models.QuerySet:
        """Annotate the queryset with ledger data"""
        return (
            queryset.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_mission_income()
            .annotate_incursion_income()
            .annotate_daily_goal_income()
            .annotate_citadel_income()
            .annotate_miscellaneous()
        )

    def generate_ledger_alliance(self, alliance_id: int) -> models.QuerySet:
        # Filter Corporations
        qs = self.filter(
            Q(division__corporation__corporation__alliance__alliance_id=alliance_id)
        )
        # Get all Character IDs
        entity_ids_second = self.values_list("second_party_id", flat=True)
        entity_ids_first = self.values_list("first_party_id", flat=True)
        entity_ids = set(entity_ids_first) | set(entity_ids_second)

        # Filter queryset with the linked characters
        qs = qs.filter(
            Q(first_party_id__in=entity_ids) | Q(second_party_id__in=entity_ids)
        )

        # Exclude Tax Events
        qs = events_filter(qs)

        return qs

    def generate_ledger(self) -> models.QuerySet:
        """Generate the ledger for the corporation"""
        # Get all Character IDs
        entity_ids_second = self.values_list("second_party_id", flat=True)
        entity_ids_first = self.values_list("first_party_id", flat=True)
        entity_ids = set(entity_ids_first) | set(entity_ids_second)

        # Get all linked Characters
        main_and_alts, chars_list = self._get_linked_chars(entity_ids)

        # Filter queryset with the linked characters
        qs = self.filter(
            Q(first_party_id__in=chars_list) | Q(second_party_id__in=chars_list)
        )
        # Exclude Tax Events
        qs = events_filter(qs)

        # Annotate the queryset
        qs = self._annotate_main_and_alts(qs, main_and_alts, entity_ids)

        return qs

    # pylint: disable=duplicate-code
    def aggregate_amounts_information_modal_character(
        self,
        amounts: defaultdict,
        filter_date: timezone.datetime,
        character_ids: list,
    ) -> dict:
        """Generate information data for the corporation modal view"""
        # Define the type names
        type_names = [
            "ess_income",
            "daily_goal_income",
        ]

        qs = self

        # Filter Characters
        qs = qs.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids)
        )

        # Exclude Corp Tax Events
        qs = events_filter(qs)

        # Annotate the queryset
        qs = self.annotate_ledger_data(qs)

        # Create the annotations
        annotations = _annotations_information(filter_date, type_names)

        qs = qs.aggregate(**annotations)

        # Assign the results to the amounts dictionary
        for type_name in type_names:
            amounts[type_name]["total_amount"] = self._convert_corp_tax(
                qs[f"{type_name}_total_amount"]
            )
            amounts[type_name]["total_amount_day"] = self._convert_corp_tax(
                qs[f"{type_name}_total_amount_day"]
            )
            amounts[type_name]["total_amount_hour"] = self._convert_corp_tax(
                qs[f"{type_name}_total_amount_hour"]
            )

        return amounts

    # pylint: disable=duplicate-code
    def aggregate_amounts_information_modal_corporation(
        self,
        amounts: defaultdict,
        filter_date: timezone.datetime,
        corporation_id: int,
        character_ids: list,
    ) -> dict:
        """Generate information data for the corporation modal view"""
        # Define the type names
        type_names = [
            "bounty_income",
            "ess_income",
            "daily_goal_income",
            "mission_income",
            "citadel_income",
            "incursion_income",
        ]

        qs = self

        # Filter Corporations
        qs = self.filter(
            Q(division__corporation__corporation__corporation_id=corporation_id)
        )

        # Filter Characters
        qs = qs.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids)
        )

        # Exclude Corp Tax Events
        qs = events_filter(qs)

        # Annotate the queryset
        qs = self.annotate_ledger_data(qs)

        # Create the annotations
        annotations = _annotations_information(filter_date, type_names)

        qs = qs.aggregate(**annotations)

        # Assign the results to the amounts dictionary
        for type_name in type_names:
            amounts[type_name]["total_amount"] = qs[f"{type_name}_total_amount"]
            amounts[type_name]["total_amount_day"] = qs[f"{type_name}_total_amount_day"]
            amounts[type_name]["total_amount_hour"] = qs[
                f"{type_name}_total_amount_hour"
            ]

        return amounts

    # pylint: disable=duplicate-code
    def aggregate_amounts_information_modal_alliance(
        self,
        amounts: defaultdict,
        filter_date: timezone.datetime,
        corporations: list,
    ) -> dict:
        """Generate data template for the ledger character information view"""
        # Define the type names
        type_names = [
            "bounty_income",
            "ess_income",
            "daily_goal_income",
            "mission_income",
            "citadel_income",
            "incursion_income",
        ]

        qs = self

        # Filter Corporations
        qs = self.filter(
            Q(division__corporation__corporation__corporation_id__in=corporations)
        )

        # Exclude Corp Tax Events
        qs = events_filter(qs)

        # Annotate the queryset
        qs = self.annotate_ledger_data(qs)

        # Create the annotations
        annotations = _annotations_information(filter_date, type_names)

        qs = qs.aggregate(**annotations)

        # Assign the results to the amounts dictionary
        for type_name in type_names:
            amounts[type_name]["total_amount"] = qs[f"{type_name}_total_amount"]
            amounts[type_name]["total_amount_day"] = qs[f"{type_name}_total_amount_day"]
            amounts[type_name]["total_amount_hour"] = qs[
                f"{type_name}_total_amount_hour"
            ]

        return amounts

    def annotate_billboard(self, chars: list) -> models.QuerySet:
        qs = self.filter(Q(first_party_id__in=chars) | Q(second_party_id__in=chars))
        # Exclude Corp Tax Events
        qs = events_filter(qs)
        return qs


class CorpWalletManagerBase(models.Manager):
    pass


CorpWalletManager = CorpWalletManagerBase.from_queryset(CorpWalletQuerySet)
