from ninja import Field, Schema
from ninja.pagination import LimitOffsetPagination
from ninja.types import DictStrAny

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet

from allianceauth.authentication.models import UserProfile
from allianceauth.eveonline.models import EveCharacter

from ledger import app_settings, models

if app_settings.LEDGER_CORPSTATS_TWO:
    from corpstats.models import CorpMember
else:
    from allianceauth.corputils.models import CorpMember

from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class Paginator(LimitOffsetPagination):
    class Input(Schema):
        limit: int = Field(30000, ge=1)
        offset: int = Field(0, ge=0)

    # pylint: disable=unused-argument
    def paginate_queryset(
        self,
        queryset: QuerySet,
        pagination: Input,
        **params: DictStrAny,  # pylint: disable=unused-import
    ) -> any:
        offset = pagination.offset
        limit: int = pagination.limit
        return {
            "items": queryset[offset : offset + limit],
            "count": self._items_count(queryset),
        }


# pylint: disable=import-outside-toplevel
def get_models_and_string():
    if app_settings.LEDGER_MEMBERAUDIT_USE:
        from memberaudit.models import (
            CharacterMiningLedgerEntry as CharacterMiningLedger,
        )
        from memberaudit.models import CharacterWalletJournalEntry

        return (
            CharacterMiningLedger,
            CharacterWalletJournalEntry,
            "character__eve_character",
        )
    from ledger.models.characteraudit import (
        CharacterMiningLedger,
        CharacterWalletJournalEntry,
    )

    return (
        CharacterMiningLedger,
        CharacterWalletJournalEntry,
        "character__character",
    )


def get_main_character(request, character_id):
    perms = True

    main_char = EveCharacter.objects.select_related(
        "character_ownership",
        "character_ownership__user__profile",
        "character_ownership__user__profile__main_character",
    ).get(character_id=character_id)
    try:
        main_char = main_char.character_ownership.user.profile.main_character
    except ObjectDoesNotExist:
        pass

    # check access
    visible = models.CharacterAudit.objects.visible_eve_characters(request.user)
    if main_char not in visible:
        account_chars = (
            request.user.profile.main_character.character_ownership.user.character_ownerships.all()
        )
        logger.warning(
            "%s Can See %s, requested %s",
            request.user,
            list(visible),
            main_char.id,
        )
        if main_char in account_chars:
            pass
        else:
            perms = False

    if not request.user.has_perm("ledger.basic_access"):
        logger.warning(
            "%s does not have Perm requested, Requested %s", request.user, main_char.id
        )
        perms = False

    return perms, main_char


def get_alts_queryset(main_char):
    try:
        linked_characters = (
            main_char.character_ownership.user.character_ownerships.all().values_list(
                "character_id", flat=True
            )
        )

        return EveCharacter.objects.filter(id__in=linked_characters)
    except ObjectDoesNotExist:
        return EveCharacter.objects.filter(pk=main_char.pk)


def get_main_and_alts_all(corporations: list, char_ids=False, corp_members=True):
    """
    Get all mains and their alts from Alliance Auth if they are in Corp

    Args:
    - corporations: corp `list`
    - char_ids: include list
    - corp_members: add Corp Members

    Returns - Dict (Queryset)
    - `Dict`: Mains and Alts

    Returns - Dict(Queryset) & List
    - `Dict`: Mains and Alts Queryset
    - `List`: Character IDS
    """

    # TODO users profile filter corporation über main char und alt chars corp ids

    mains = {}

    # pylint: disable=no-member
    users = (
        UserProfile.objects.select_related("main_character")
        .all()
        .order_by("main_character_id")
    )

    for char in users:
        try:
            if char.main_character:
                main = (
                    char.main_character.character_ownership.user.profile.main_character
                )
                linked_characters = (
                    main.character_ownership.user.character_ownerships.all().exclude(
                        character__character_id=main.character_id
                    )
                )

                if main.corporation_id in corporations:
                    mains[main.character_id] = {
                        "main": main,
                        "alts": [char.character for char in linked_characters],
                    }
            else:
                continue
        except ObjectDoesNotExist:
            pass

    if corp_members:
        corp = CorpMember.objects.select_related("corpstats", "corpstats__corp").filter(
            corpstats__corp__corporation_id__in=corporations
        )

        # Add None Registred Chars to the Ledger
        chars = list(
            set(
                [main["main"].character_id for _, main in mains.items()]
                + [
                    alt.character_id
                    for _, main in mains.items()
                    for alt in main["alts"]
                ]
            )
        )
        if corp:
            for char in corp:
                if char.character_id not in chars:
                    mains[char.character_id] = {"main": char, "alts": []}

    # Sort Names Alphabetic
    mains = sorted(mains.items(), key=lambda item: item[1]["main"].character_name)
    mains = dict(mains)

    if char_ids:
        chars = list(
            set(
                [main["main"].character_id for _, main in mains.items()]
                + [
                    alt.character_id
                    for _, main in mains.items()
                    for alt in main["alts"]
                ]
            )
        )
        return mains, chars

    return mains


def get_corporations(request, character_id):  # pylint: disable=unused-argument
    main_char = EveCharacter.objects.select_related(
        "character_ownership",
        "character_ownership__user__profile",
        "character_ownership__user__profile__main_character",
    ).get(character_id=character_id)
    try:
        main_char = main_char.character_ownership.user.profile.main_character
    except ObjectDoesNotExist:
        pass

    try:
        linked_characters = (
            main_char.character_ownership.user.character_ownerships.all().values_list(
                "character_id", flat=True
            )
        )
        chars = EveCharacter.objects.filter(id__in=linked_characters)

        corporations = set()

        for char in chars:
            corporations.add(char.corporation_id)

        return corporations
    except ObjectDoesNotExist:
        char = EveCharacter.objects.filter(pk=main_char.pk)
        corporations = set()

        for char in chars:
            corporations.add(char.corporation_id)

        return corporations
