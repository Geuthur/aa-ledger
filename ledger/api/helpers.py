from django.core.exceptions import ObjectDoesNotExist

from allianceauth.eveonline.models import EveCharacter

from ledger import app_settings, models
from ledger.errors import LedgerImportError
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


def convert_ess_payout(ess: int) -> float:
    return (ess / app_settings.LEDGER_CORP_TAX) * (100 - app_settings.LEDGER_CORP_TAX)


# pylint: disable=import-outside-toplevel
def get_models_and_string():
    if app_settings.LEDGER_MEMBERAUDIT_USE:
        try:
            from memberaudit.models import (
                CharacterMiningLedgerEntry as CharacterMiningLedger,
            )
            from memberaudit.models import CharacterWalletJournalEntry

            return (
                CharacterMiningLedger,
                CharacterWalletJournalEntry,
            )
        except ImportError as exc:
            logger.error("Memberaudit is enabled but not installed")
            raise LedgerImportError("Memberaudit is enabled but not installed") from exc

    from ledger.models.characteraudit import (
        CharacterMiningLedger,
        CharacterWalletJournalEntry,
    )

    return (
        CharacterMiningLedger,
        CharacterWalletJournalEntry,
    )


# pylint: disable=import-outside-toplevel
def get_corp_models_and_string():
    if app_settings.LEDGER_CORPSTATS_TWO:
        try:
            from corpstats.models import CorpMember

            return CorpMember
        except ImportError as exc:
            logger.error("Corpstats is enabled but not installed")
            raise LedgerImportError("Corpstats is enabled but not installed") from exc

    from allianceauth.corputils.models import CorpMember

    return CorpMember


def get_main_character(request, character_id):
    perms = True
    if character_id == 0:
        character_id = request.user.profile.main_character.character_id

    main_char = EveCharacter.objects.select_related(
        "character_ownership",
        "character_ownership__user__profile",
        "character_ownership__user__profile__main_character",
    ).get(character_id=character_id)
    # pylint: disable=broad-exception-caught
    try:
        main_char = main_char.character_ownership.user.profile.main_character
    except Exception:
        pass

    # check access
    visible = models.CharacterAudit.objects.visible_eve_characters(request.user)
    if main_char not in visible:
        account_chars = (
            request.user.profile.main_character.character_ownership.user.character_ownerships.all()
        )
        account_char_ids = account_chars.values_list("character_id", flat=True)

        logger.warning(
            "%s Can See %s, requested %s",
            request.user,
            list(visible),
            main_char.id,
        )

        if main_char.id not in account_char_ids:
            perms = False

    if not request.user.has_perm("ledger.basic_access"):
        logger.warning(
            "%s does not have Perm requested, Requested %s", request.user, main_char.id
        )
        perms = False

    return perms, main_char


def get_character(request, character_id):
    perms = True
    if character_id == 0:
        character_id = request.user.profile.main_character.character_id

    main_char = EveCharacter.objects.select_related(
        "character_ownership",
        "character_ownership__user__profile",
        "character_ownership__user__profile__main_character",
    ).get(character_id=character_id)

    # check access
    visible = models.CharacterAudit.objects.visible_eve_characters(request.user)
    if main_char not in visible:
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


def get_main_and_alts_all(corporations: list, corp_members=True):
    """
    Get all mains and their alts from given corporations

    Args:
    - corporations: corp `list`
    - corp_members: add Corp Members

    Returns - Dict(Queryset) & List
    - `Dict`: Mains and Alts Queryset
    - `List`: Character IDS
    """
    mains = {}
    chars_list = set()
    corpmember = get_corp_models_and_string()

    linked_chars = EveCharacter.objects.filter(corporation_id__in=corporations)
    linked_chars = linked_chars | EveCharacter.objects.filter(
        character_ownership__user__profile__main_character__corporation_id__in=corporations
    )

    linked_chars = linked_chars.select_related(
        "character_ownership", "character_ownership__user__profile__main_character"
    ).prefetch_related("character_ownership__user__character_ownerships")
    linked_chars = linked_chars.order_by("character_name")

    for char in linked_chars:
        try:
            main = char.character_ownership.user.profile.main_character
            if main is not None:
                linked_characters = (
                    main.character_ownership.user.character_ownerships.all().exclude(
                        character__character_id=main.character_id
                    )
                )
                if main.corporation_id in corporations:
                    alts = [char.character for char in linked_characters]
                    mains[main.character_id] = {
                        "main": main,
                        "alts": alts,
                    }
                chars_list.add(main.character_id)
                for alt in alts:
                    chars_list.add(alt.character_id)

        except ObjectDoesNotExist:
            pass

    if corp_members:
        corp = corpmember.objects.select_related("corpstats", "corpstats__corp").filter(
            corpstats__corp__corporation_id__in=corporations
        )

        for char in corp:
            try:
                char = EveCharacter.objects.get(character_id=char.character_id)
            except EveCharacter.DoesNotExist:
                pass
            if char.character_id not in chars_list:
                mains[char.character_id] = {"main": char, "alts": []}
                chars_list.add(char.character_id)
    return mains, list(chars_list)


def get_corporations(request):
    linked_characters = request.user.profile.main_character.character_ownership.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    chars = EveCharacter.objects.filter(id__in=linked_characters)

    corporations = set()

    for char in chars:
        corporations.add(char.corporation_id)

    return corporations
