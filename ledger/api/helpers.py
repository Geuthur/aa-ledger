from django.core.exceptions import ObjectDoesNotExist

from allianceauth.eveonline.models import EveCharacter

from ledger import app_settings, models
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


def convert_ess_payout(ess: int) -> float:
    """Convert ESS payout"""
    return (ess / app_settings.LEDGER_CORP_TAX) * (100 - app_settings.LEDGER_CORP_TAX)


def get_character(request, character_id):
    """Get Character and check permissions"""
    perms = True
    if character_id == 0:
        character_id = request.user.profile.main_character.character_id

    try:
        main_char = EveCharacter.objects.get(character_id=character_id)
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
        corporations = get_main_and_alts_ids_corporations(request)
    else:
        corporations = [corporation_id]

    main_corp = models.CorporationAudit.objects.filter(
        corporation__corporation_id__in=corporations
    )
    # Check access
    visible = models.CorporationAudit.objects.visible_to(request.user)
    # Check if there is an intersection between main_corp and visible
    common_corps = main_corp.intersection(visible)
    if not common_corps.exists():
        perms = False
    return perms, main_corp.values_list("corporation__corporation_id", flat=True)


def get_alliance(request, alliance_id):
    """Get Alliance and check permissions for each corporation"""
    perms = True
    if alliance_id == 0:
        alliances = get_main_and_alts_ids_alliances(request)
    else:
        alliances = [alliance_id]

    main_corp = models.CorporationAudit.objects.filter(
        corporation__alliance__alliance_id__in=alliances
    )

    # Check access
    visible = models.CorporationAudit.objects.visible_to(request.user)

    # Check if there is an intersection between main_corp and visible
    common_corps = main_corp.intersection(visible)
    if not common_corps.exists():
        perms = False
    return perms, main_corp.values_list("corporation__alliance__alliance_id", flat=True)


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


def _get_linked_characters(corporations):
    linked_chars = EveCharacter.objects.filter(corporation_id__in=corporations)
    linked_chars |= EveCharacter.objects.filter(
        character_ownership__user__profile__main_character__corporation_id__in=corporations
    )
    return (
        linked_chars.select_related(
            "character_ownership", "character_ownership__user__profile__main_character"
        )
        .prefetch_related("character_ownership__user__character_ownerships")
        .order_by("character_name")
    )


def get_main_and_alts_ids_all(corporations: list) -> list:
    """Get all members for given corporations"""
    chars_list = set()

    linked_chars = _get_linked_characters(corporations)

    for char in linked_chars:
        chars_list.add(char.character_id)

    return list(chars_list)


def get_main_and_alts_ids_corporations(request) -> list:
    linked_characters = request.user.profile.main_character.character_ownership.user.character_ownerships.select_related(
        "character", "user"
    ).all()

    linked_characters = linked_characters.values_list("character_id", flat=True)
    chars = EveCharacter.objects.filter(id__in=linked_characters)

    corporations = set()

    for char in chars:
        corporations.add(char.corporation_id)

    return list(corporations)


def get_main_and_alts_ids_alliances(request) -> list:
    linked_characters = request.user.profile.main_character.character_ownership.user.character_ownerships.select_related(
        "character", "user"
    ).all()

    linked_characters = linked_characters.values_list("character_id", flat=True)
    chars = EveCharacter.objects.filter(id__in=linked_characters)

    alliances = set()

    for char in chars:
        alliances.add(char.alliance_id)

    return list(alliances)
