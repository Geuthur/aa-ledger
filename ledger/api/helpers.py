from django.core.exceptions import ObjectDoesNotExist

from allianceauth.eveonline.models import EveCharacter

from ledger import app_settings, models
from ledger.errors import LedgerImportError
from ledger.hooks import get_extension_logger
from ledger.tasks import create_missing_character

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


def get_character(request, character_id):
    """Get Character and check permissions"""
    perms = True
    if character_id == 0:
        character_id = request.user.profile.main_character.character_id

    try:
        main_char = EveCharacter.objects.select_related(
            "character_ownership",
            "character_ownership__user__profile",
            "character_ownership__user__profile__main_character",
        ).get(character_id=character_id)
    except ObjectDoesNotExist:
        main_char = EveCharacter.objects.select_related(
            "character_ownership",
            "character_ownership__user__profile",
            "character_ownership__user__profile__main_character",
        ).get(character_id=request.user.profile.main_character.character_id)

    # check access
    visible = models.CharacterAudit.objects.visible_eve_characters(request.user)
    if main_char not in visible:
        perms = False
    return perms, main_char


def get_corporation(request, corporation_id):
    """Get Corporation and check permissions"""
    perms = True
    if corporation_id == 0:
        corporations = get_main_and_alts_corporations(request)
    else:
        corporations = [corporation_id]
    try:
        main_corp = models.CorporationAudit.objects.filter(
            corporation__corporation_id__in=corporations
        )
    except ObjectDoesNotExist:
        main_corp = None
    # Check access
    visible = models.CorporationAudit.objects.visible_to(request.user)
    # Check if there is an intersection between main_corp and visible
    common_corps = main_corp.intersection(visible)
    if not common_corps.exists():
        perms = False
    return perms, main_corp


def get_alts_queryset(main_char, corporations=None):
    """Get all alts for a main character, optionally filtered by corporations."""
    try:
        linked_corporations = (
            main_char.character_ownership.user.character_ownerships.all()
        )

        if corporations:
            linked_corporations = linked_corporations.filter(
                character__corporation_id__in=corporations
            )

        linked_corporations = linked_corporations.values_list("character_id", flat=True)

        return EveCharacter.objects.filter(id__in=linked_corporations)
    except ObjectDoesNotExist:
        return EveCharacter.objects.filter(pk=main_char.pk)


def get_main_and_alts_all(main_corp: list):
    """Get all members for a corporation"""
    characters = {}
    chars_list = set()
    corps_list = main_corp
    missing_chars = set()

    linked_chars = EveCharacter.objects.filter(corporation_id__in=corps_list)
    linked_chars = linked_chars | EveCharacter.objects.filter(
        character_ownership__user__profile__main_character__corporation_id__in=corps_list
    )

    linked_chars = linked_chars.select_related(
        "character_ownership", "character_ownership__user__profile__main_character"
    ).prefetch_related("character_ownership__user__character_ownerships")

    linked_chars = linked_chars.order_by("character_name")

    corpmember = get_corp_models_and_string()

    for char in linked_chars:
        try:
            main = char.character_ownership.user.profile.main_character
            if main is not None:
                if main.character_id not in characters:
                    characters[main.character_id] = {
                        "main": main,
                        "alts": [],
                    }
                characters[main.character_id]["alts"].append(char)
                chars_list.add(char.character_id)
        except ObjectDoesNotExist:
            continue

    for member in corpmember.objects.filter(
        corpstats__corp__corporation_id__in=corps_list
    ).exclude(character_id__in=chars_list):
        try:
            char = (
                EveCharacter.objects.select_related(
                    "character_ownership",
                    "character_ownership__user__profile__main_character",
                )
                .prefetch_related("character_ownership__user__character_ownerships")
                .get(character_id=member.character_id)
            )
            main = char.character_ownership.user.profile.main_character
            if main is not None:
                if main.character_id not in characters:
                    characters[main.character_id] = {
                        "main": main,
                        "alts": [],
                    }
                characters[main.character_id]["alts"].append(member.character)
                chars_list.add(member.character_id)
        except ObjectDoesNotExist:
            # Ensure that the character not already exists
            if EveCharacter.objects.filter(character_id=member.character_id).exists():
                char = EveCharacter.objects.get(character_id=member.character_id)
                characters[char.character_id] = {
                    "main": char,
                    "alts": [char],
                }
                if char.corporation_id in corps_list:
                    chars_list.add(char.character_id)
                continue
            missing_chars.add(member.character_id)
    try:
        create_missing_character.apply_async(
            args=missing_chars,
            priority=6,
        )
    # pylint: disable=broad-exception-caught
    except Exception as exc:
        logger.debug("Error: %s", exc)

    return characters, list(chars_list)


def get_main_and_alts_corporations(request):
    linked_characters = request.user.profile.main_character.character_ownership.user.character_ownerships.select_related(
        "character", "user"
    ).all()

    linked_characters = linked_characters.values_list("character_id", flat=True)
    chars = EveCharacter.objects.filter(id__in=linked_characters)

    corporations = set()

    for char in chars:
        corporations.add(char.corporation_id)

    return list(corporations)
