import json
from collections import defaultdict

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter

from ledger.hooks import get_extension_logger
from ledger.view_helpers.core import events_filter

logger = get_extension_logger(__name__)


class CorpWalletQuerySet(models.QuerySet):
    def _get_linked_chars(self, corporations: list, chars_ids: list) -> dict:
        linked_chars = EveCharacter.objects.filter(corporation_id__in=corporations)
        linked_chars |= EveCharacter.objects.filter(
            character_ownership__user__profile__main_character__corporation_id__in=corporations
        )
        linked_chars = linked_chars.select_related(
            "character_ownership", "character_ownership__user__profile__main_character"
        ).prefetch_related("character_ownership__user__character_ownerships__character")

        seond_party_ids = self.filter(
            division__corporation__corporation__corporation_id__in=corporations,
            ref_type="bounty_prizes",
        ).values_list("second_party_id", flat=True)

        char_to_main = {}
        chars_list = []
        for char in linked_chars:
            try:
                if char.corporation_id in corporations:
                    main_char = char.character_ownership.user.profile.main_character
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

        # Add all Chars that not registred
        for character_id in seond_party_ids:
            if character_id not in chars_list:
                char_to_main[character_id] = [character_id]
                chars_list.append(character_id)

        return char_to_main, chars_list

    def annotate_bounty(self, second_party_ids: list) -> models.QuerySet:
        return self.annotate(
            total_bounty=Coalesce(
                models.Sum(
                    "amount",
                    filter=(
                        models.Q(ref_type="bounty_prizes")
                        & models.Q(second_party_id__in=second_party_ids)
                    ),
                ),
                models.Value(0),
                output_field=models.DecimalField(),
            )
        )

    def annotate_ess(self, second_party_ids: list) -> models.QuerySet:
        qs = events_filter(self)
        return qs.annotate(
            total_ess=Coalesce(
                models.Sum(
                    "amount",
                    filter=(
                        models.Q(ref_type="ess_escrow_transfer")
                        & models.Q(second_party_id__in=second_party_ids)
                    ),
                ),
                models.Value(0),
                output_field=models.DecimalField(),
            )
        )

    def annotate_ledger(self, corporations: list) -> models.QuerySet:
        char_ids = self.values_list("second_party_id", flat=True)
        main_and_alts, chars_list = self._get_linked_chars(corporations, char_ids)

        # Create a subquery to get the main character id
        main_subquery = models.Case(
            *[
                models.When(second_party_id__in=char_ids, then=main_id)
                for main_id, char_ids in main_and_alts.items()
            ],
            output_field=models.IntegerField(),
        )

        # Create a subquery to get the alts
        alts_subquery = models.Case(
            *[
                models.When(
                    second_party_id__in=char_ids,
                    then=models.Value(json.dumps(char_ids)),
                )
                for _, char_ids in main_and_alts.items()
            ],
            output_field=models.JSONField(),
        )

        # First annotation step
        queryset = self.filter(second_party_id__in=chars_list).annotate(
            main_character_id=main_subquery,
            main_character_name=Coalesce(
                models.Subquery(
                    EveCharacter.objects.filter(
                        character_id=models.OuterRef("main_character_id")
                    ).values("character_name")[:1]
                ),
                models.Value("Unknown"),
            ),
            alts=alts_subquery,
        )

        return (
            queryset.values(
                "main_character_id", "main_character_name", "alts"
            )  # Group by main_character_id
            .annotate(
                total_bounty=Coalesce(
                    models.Sum("amount", filter=models.Q(ref_type="bounty_prizes")),
                    models.Value(0),
                    output_field=models.DecimalField(),
                ),
                total_ess=Coalesce(
                    models.Sum(
                        "amount", filter=models.Q(ref_type="ess_escrow_transfer")
                    ),
                    models.Value(0),
                    output_field=models.DecimalField(),
                ),
            )
            .filter(models.Q(total_bounty__gt=0) | models.Q(total_ess__gt=0))
        )

    def generate_template(
        self,
        amounts: defaultdict,
        character_ids: list,
        filter_date: timezone.datetime,
        mode=None,
    ) -> dict:
        qs = self.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids)
        )

        # Define the types and their respective filters
        types_filters = {
            "ess": Q(ref_type__in=["ess_escrow_transfer"]),
        }

        if mode == "corporation":
            types_filters["bounty"] = Q(ref_type__in=["bounty_prizes"])

        # Create the template
        for type_name, type_filter in types_filters.items():
            total_amount = qs.filter(type_filter).aggregate(
                total_amount=Coalesce(
                    Sum("amount"), Value(0), output_field=DecimalField()
                )
            )["total_amount"]

            total_amount_day = qs.filter(
                type_filter,
                date__year=filter_date.year,
                date__month=filter_date.month,
                date__day=filter_date.day,
            ).aggregate(
                total_amount_day=Coalesce(
                    Sum("amount"), Value(0), output_field=DecimalField()
                )
            )[
                "total_amount_day"
            ]

            total_amount_hour = qs.filter(
                type_filter,
                date__year=filter_date.year,
                date__month=filter_date.month,
                date__day=filter_date.day,
                date__hour=filter_date.hour,
            ).aggregate(
                total_amount_hour=Coalesce(
                    Sum("amount"), Value(0), output_field=DecimalField()
                )
            )[
                "total_amount_hour"
            ]

            amounts[type_name]["total_amount"] = total_amount
            amounts[type_name]["total_amount_day"] = total_amount_day
            amounts[type_name]["total_amount_hour"] = total_amount_hour

        return amounts


class CorpWalletManagerBase(models.Manager):
    pass


CorpWalletManager = CorpWalletManagerBase.from_queryset(CorpWalletQuerySet)
