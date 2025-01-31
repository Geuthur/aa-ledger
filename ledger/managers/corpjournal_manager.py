import json
from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Case, DecimalField, F, Q, Sum, Value, When
from django.db.models.functions import Coalesce, Round
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter

from ledger import app_settings
from ledger.hooks import get_extension_logger
from ledger.models.general import EveEntity
from ledger.view_helpers.core import events_filter

logger = get_extension_logger(__name__)

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
        # Exclude Tax Events
        qs = events_filter(self)
        if is_character_ledger:
            return qs.annotate(
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
        return qs.annotate(
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
        char_to_main = {}
        entity_list = []

        linked_chars = EveCharacter.objects.filter(character_id__in=entity_ids)
        linked_chars |= EveCharacter.objects.filter(
            character_ownership__user__profile__main_character__character_id__in=entity_ids
        )
        linked_chars = linked_chars.select_related(
            "character_ownership", "character_ownership__user__profile__main_character"
        ).prefetch_related("character_ownership__user__character_ownerships__character")

        # Get Registered Characters
        for char in linked_chars:
            try:
                try:
                    main_char = char.character_ownership.user.profile.main_character
                except ObjectDoesNotExist:
                    main_char = char
                main_char_id = main_char.character_id
                if main_char_id not in char_to_main:
                    char_to_main[main_char_id] = []
                if char.character_id in entity_ids:
                    char_to_main[main_char_id].append(char.character_id)
                    entity_list.append(char.character_id)
            except AttributeError:
                continue

        missing_entitys = set(entity_ids) - set(entity_list)

        entitys = EveEntity.objects.filter(eve_id__in=missing_entitys)
        # Get All Eve Entities
        for entity in entitys:
            try:
                main_char_id = entity.eve_id
                if main_char_id not in char_to_main:
                    char_to_main[main_char_id] = []
                char_to_main[main_char_id].append(entity.eve_id)
                entity_list.append(entity.eve_id)
            except AttributeError:
                continue

        missing_entitys = set(entity_ids) - set(entity_list)

        return char_to_main, set(entity_list)

    def get_ledger_data(self, queryset) -> models.QuerySet:
        """Get the ledger data"""
        return (
            queryset.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_mission_income()
            .annotate_incursion_income()
            .annotate_daily_goal_income()
            .annotate_citadel_income()
            .annotate_miscellaneous()
        )

    def generate_ledger(self, corporations: list) -> models.QuerySet:
        """Generate the ledger for the corporation"""
        # Filter Corporations6
        qs = self.filter(
            Q(division__corporation__corporation__corporation_id__in=corporations)
        )
        # Get all Character IDs
        entity_ids_second = self.values_list("second_party_id", flat=True).distinct()
        entity_ids_first = self.values_list("first_party_id", flat=True).distinct()
        entity_ids = set(entity_ids_first) | set(entity_ids_second)

        # Get all linked Characters
        main_and_alts, entity_ids = self._get_linked_chars(entity_ids)

        # Filter queryset with the linked characters
        qs = qs.filter(
            Q(first_party_id__in=entity_ids) | Q(second_party_id__in=entity_ids)
        )
        # Exclude Tax Events
        qs = events_filter(qs)

        # Annotate the queryset
        qs = qs.annotate(
            main_entity_id=Case(
                *[
                    When(
                        (
                            Q(second_party_id__in=alt_ids)
                            | (Q(first_party_id__in=alt_ids))
                        ),
                        then=Value(main_id),
                    )
                    for main_id, alt_ids in main_and_alts.items()
                ],
                output_field=models.IntegerField(),
            ),
            alts=Case(
                *[
                    When(
                        (
                            Q(second_party_id__in=alt_ids)
                            | (Q(first_party_id__in=alt_ids))
                        ),
                        then=Value(json.dumps(alt_ids)),
                    )
                    for _, alt_ids in main_and_alts.items()
                ],
                default=Value("[]"),
                output_field=models.JSONField(),
            ),
        ).values("main_entity_id", "alts")

        qs = self.get_ledger_data(qs)

        return qs

    # pylint: disable=duplicate-code, too-many-positional-arguments
    def generate_template(
        self,
        amounts: defaultdict,
        filter_date: timezone.datetime,
        character_ids: list,
        corporations_ids: list,
        entity_type=None,
    ) -> dict:
        """Generate data template for the ledger character information view"""
        # Define the type names
        type_names = [
            "ess_income",
            "daily_goal_income",
        ]

        if entity_type == "corporation":
            type_names += [
                "bounty_income",
                "mission_income",
                "citadel_income",
                "incursion_income",
            ]
        qs = self

        # Filter Corporations
        qs = self.filter(
            Q(division__corporation__corporation__corporation_id__in=corporations_ids)
        )
        # Filter Characters
        qs = qs.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids)
        )

        # Exclude Corp Tax Events
        qs = events_filter(qs)

        # Annotate the queryset
        qs = self.get_ledger_data(qs)

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

        # Assign the results to the amounts dictionary
        for type_name in type_names:
            if entity_type != "corporation":
                amounts[type_name]["total_amount"] = self._convert_corp_tax(
                    qs[f"{type_name}_total_amount"]
                )
                amounts[type_name]["total_amount_day"] = self._convert_corp_tax(
                    qs[f"{type_name}_total_amount_day"]
                )
                amounts[type_name]["total_amount_hour"] = self._convert_corp_tax(
                    qs[f"{type_name}_total_amount_hour"]
                )
            else:
                amounts[type_name]["total_amount"] = qs[f"{type_name}_total_amount"]
                amounts[type_name]["total_amount_day"] = qs[
                    f"{type_name}_total_amount_day"
                ]
                amounts[type_name]["total_amount_hour"] = qs[
                    f"{type_name}_total_amount_hour"
                ]

        return amounts

    def annotate_billboard(self, chars: list) -> models.QuerySet:
        qs = self.filter(Q(first_party_id__in=chars) | Q(second_party_id__in=chars))
        # Exclude Corp Tax Events
        qs = events_filter(qs)

        qs = self.get_ledger_data(qs)
        return qs


class CorpWalletManagerBase(models.Manager):
    pass


CorpWalletManager = CorpWalletManagerBase.from_queryset(CorpWalletQuerySet)
