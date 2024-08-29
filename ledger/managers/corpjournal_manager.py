from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Case, DecimalField, OuterRef, Q, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce

from allianceauth.eveonline.models import EveCharacter

from ledger.hooks import get_corp_models_and_string, get_extension_logger
from ledger.view_helpers.core import events_filter

logger = get_extension_logger(__name__)


class CorpWalletQuerySet(models.QuerySet):
    def _get_linked_chars(self, corporations: list) -> dict:
        linked_chars = EveCharacter.objects.filter(corporation_id__in=corporations)
        linked_chars |= EveCharacter.objects.filter(
            character_ownership__user__profile__main_character__corporation_id__in=corporations
        )
        linked_chars = linked_chars.select_related(
            "character_ownership", "character_ownership__user__profile__main_character"
        ).prefetch_related("character_ownership__user__character_ownerships__character")

        corpmember = get_corp_models_and_string()
        char_to_main = {}
        main_to_alts = {}
        for char in linked_chars:
            try:
                if char.corporation_id in corporations:
                    main_char = char.character_ownership.user.profile.main_character
                    main_char_id = main_char.character_id
                    char_to_main[char.character_id] = main_char_id
                if main_char_id not in main_to_alts:
                    main_to_alts[main_char_id] = []
                main_to_alts[main_char_id].append(char.character_id)
            except ObjectDoesNotExist:
                continue
            except AttributeError:
                continue

        corpmember = (
            corpmember.objects.filter(corpstats__corp__corporation_id__in=corporations)
            .values_list("character_id", flat=True)
            .exclude(character_id__in=char_to_main)
        )

        for character_id in corpmember:
            char_to_main[character_id] = character_id
        return char_to_main, main_to_alts

    def annotate_bounty(self, second_party_ids: list) -> models.QuerySet:
        return self.annotate(
            total_bounty=Coalesce(
                Sum(
                    "amount",
                    filter=(
                        Q(ref_type="bounty_prizes")
                        & Q(second_party_id__in=second_party_ids)
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_ess(self, second_party_ids: list) -> models.QuerySet:
        qs = events_filter(self)
        return qs.annotate(
            total_ess=Coalesce(
                Sum(
                    "amount",
                    filter=(
                        Q(ref_type="ess_escrow_transfer")
                        & Q(second_party_id__in=second_party_ids)
                    ),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_ledger(self, corporations: list) -> models.QuerySet:
        char_to_main, main_to_alts = self._get_linked_chars(corporations)

        # Create a subquery to map second_party_id to main_character_id
        subquery = Case(
            *[
                When(second_party_id=char_id, then=main_id)
                for char_id, main_id in char_to_main.items()
            ],
            output_field=models.IntegerField(),
        )

        return (
            self.filter(second_party_id__in=char_to_main.keys())
            .annotate(
                main_character_id=subquery,
                main_character_name=Subquery(
                    EveCharacter.objects.filter(
                        character_id=OuterRef("main_character_id")
                    ).values("character_name")[:1]
                ),
                alts=Value(
                    [
                        alt_id
                        for main_id, alts in main_to_alts.items()
                        for alt_id in alts
                        if main_id == OuterRef("main_character_id")
                    ],
                    output_field=models.JSONField(),
                ),
            )
            .values(
                "main_character_id", "main_character_name", "alts"
            )  # Group by main_character_id
            .annotate(
                total_bounty=Coalesce(
                    Sum("amount", filter=Q(ref_type="bounty_prizes")),
                    Value(0),
                    output_field=DecimalField(),
                ),
                total_ess=Coalesce(
                    Sum("amount", filter=Q(ref_type="ess_escrow_transfer")),
                    Value(0),
                    output_field=DecimalField(),
                ),
            )
            .filter(Q(total_bounty__gt=0) | Q(total_ess__gt=0))
        )


class CorpWalletManagerBase(models.Manager):
    pass


CorpWalletManager = CorpWalletManagerBase.from_queryset(CorpWalletQuerySet)
