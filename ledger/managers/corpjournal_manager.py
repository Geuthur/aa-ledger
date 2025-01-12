import json
from collections import defaultdict

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Case, DecimalField, F, Q, Sum, Value, When
from django.db.models.functions import Coalesce
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter

from ledger.hooks import get_extension_logger
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
    def annotate_bounty(self, second_party_ids: list) -> models.QuerySet:
        return self.annotate(
            total_bounty=Coalesce(
                Sum(
                    "amount",
                    filter=(BOUNTY_FILTER & Q(second_party_id__in=second_party_ids)),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_ess(self, second_party_ids: list) -> models.QuerySet:
        qs = self

        # Exclude Tax Events
        qs = events_filter(self)

        return qs.annotate(
            total_ess=Coalesce(
                Sum(
                    "amount",
                    filter=(ESS_FILTER & Q(second_party_id__in=second_party_ids)),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_mission(self, second_party_ids: list) -> models.QuerySet:
        return self.annotate(
            total_mission=Coalesce(
                Sum(
                    "amount",
                    filter=(MISSION_FILTER & Q(second_party_id__in=second_party_ids)),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_daily_goal(self, second_party_ids: list) -> models.QuerySet:
        return self.annotate(
            total_daily_goal=Coalesce(
                Sum(
                    "amount",
                    filter=(
                        DAILY_GOAL_REWARD_FILTER
                        & Q(second_party_id__in=second_party_ids)
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_citadel(self, first_party_ids: list) -> models.QuerySet:
        return self.annotate(
            total_citadel=Coalesce(
                Sum(
                    "amount",
                    filter=(CITADEL_FILTER & Q(first_party_id__in=first_party_ids)),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )


class CorpWalletQuerySet(CorpWalletQueryFilter):
    def _get_linked_chars(self, corporations: list, chars_ids: list) -> tuple:
        linked_chars = EveCharacter.objects.filter(corporation_id__in=corporations)
        linked_chars |= EveCharacter.objects.filter(
            character_ownership__user__profile__main_character__corporation_id__in=corporations
        )
        linked_chars = linked_chars.select_related(
            "character_ownership", "character_ownership__user__profile__main_character"
        ).prefetch_related("character_ownership__user__character_ownerships__character")

        char_to_main = {}
        chars_list = []

        for char in linked_chars:
            try:
                if char.corporation_id in corporations:
                    try:
                        main_char = char.character_ownership.user.profile.main_character
                    except ObjectDoesNotExist:
                        main_char = char
                    main_char_id = main_char.character_id
                    if main_char_id not in char_to_main:
                        char_to_main[main_char_id] = []
                    if char.character_id in chars_ids:
                        char_to_main[main_char_id].append(char.character_id)
                        chars_list.append(char.character_id)
            except ObjectDoesNotExist:
                continue
            except AttributeError:
                continue

        return char_to_main, set(chars_list)

    def annotate_ledger(self, corporations: list) -> models.QuerySet:
        # Filter Corporations6
        qs = self.filter(
            Q(division__corporation__corporation__corporation_id__in=corporations)
        )
        # Get all Character IDs
        char_ids_second = self.values_list("second_party_id", flat=True).distinct()
        char_ids_first = self.values_list("first_party_id", flat=True).distinct()
        char_ids = set(char_ids_first) | set(char_ids_second)
        # Get all linked Characters
        main_and_alts, char_ids = self._get_linked_chars(corporations, char_ids)

        # Filter queryset with the linked characters
        qs = qs.filter(Q(first_party_id__in=char_ids) | Q(second_party_id__in=char_ids))

        # Exclude Tax Events
        qs = events_filter(qs)

        # Annotate the queryset
        qs = (
            qs.annotate(
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
            )
            .values("main_entity_id", "alts")
            .annotate(
                total_bounty=Coalesce(
                    Sum("amount", filter=BOUNTY_FILTER),
                    Value(0),
                    output_field=DecimalField(),
                ),
                total_ess=Coalesce(
                    Sum("amount", filter=ESS_FILTER),
                    Value(0),
                    output_field=DecimalField(),
                ),
                total_miscellaneous=Coalesce(
                    Sum("amount", filter=MISC_FILTER),
                    Value(0),
                    output_field=DecimalField(),
                ),
            )
        )

        return qs

    # pylint: disable=duplicate-code, too-many-positional-arguments
    def generate_template(
        self,
        amounts: defaultdict,
        filter_date: timezone.datetime,
        character_ids: list,
        corporations_ids: list,
        mode=None,
    ) -> dict:
        # Filter Corporations
        qs = self.filter(
            Q(division__corporation__corporation__corporation_id__in=corporations_ids)
        )
        # Filter Characters
        qs = qs.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids)
        )

        # Exclude Tax Events
        qs = events_filter(qs)

        # Define the types and their respective filters
        types_filters = {
            "ess": ESS_FILTER,
        }

        # Ensure that amounts not overriden from corp journal
        if mode == "corporation":
            types_filters["bounty"] = BOUNTY_FILTER
            types_filters["mission"] = MISSION_FILTER
            types_filters["incursion"] = INCURSION_FILTER
            types_filters["daily_goal"] = DAILY_GOAL_REWARD_FILTER
            types_filters["citadel"] = CITADEL_FILTER

        annotations = {}
        # Create the template
        for type_name, type_filter in types_filters.items():
            annotations[f"{type_name}_total_amount"] = Coalesce(
                Sum(Case(When(type_filter, then=F("amount")))),
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


class CorpWalletManagerBase(models.Manager):
    pass


CorpWalletManager = CorpWalletManagerBase.from_queryset(CorpWalletQuerySet)
