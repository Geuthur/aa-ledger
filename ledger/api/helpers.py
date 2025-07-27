# Django
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet

# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__, models

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def get_character_or_none(
    request, character_id
) -> tuple[bool, models.CharacterAudit | None]:
    """Get Character and check permissions"""
    perms = True

    try:
        character = models.CharacterAudit.objects.get(
            eve_character__character_id=character_id
        )
    except ObjectDoesNotExist:
        return False, None
    except ValueError:
        return None, None

    # check access
    visible = models.CharacterAudit.objects.visible_eve_characters(request.user)
    if character.eve_character not in visible:
        perms = False
    return perms, character


def get_corporation(
    request, corporation_id
) -> tuple[bool | None, models.CorporationAudit | None]:
    """Return Corporation and check permissions"""
    perms = True

    try:
        main_corp = models.CorporationAudit.objects.get(
            corporation__corporation_id=corporation_id
        )
    except ObjectDoesNotExist:
        return None, None

    # Check access
    visible = models.CorporationAudit.objects.visible_to(request.user)
    if main_corp not in visible:
        perms = False
    return perms, main_corp


def get_manage_corporation(
    request, corporation_id
) -> tuple[bool | None, models.CorporationAudit | None]:
    """Returns a tuple of the permissions and the corporation object if manageable"""
    perms = True

    try:
        main_corp = models.CorporationAudit.objects.get(
            corporation__corporation_id=corporation_id
        )
    except ObjectDoesNotExist:
        return None, None

    # Check access
    visible = models.CorporationAudit.objects.manage_to(request.user)
    if main_corp not in visible:
        perms = False
    return perms, main_corp


def get_alliance(request, alliance_id) -> tuple[bool | None, EveAllianceInfo | None]:
    """Get Alliance and check permissions for each corporation"""
    perms = True

    corporations = models.CorporationAudit.objects.filter(
        corporation__alliance__alliance_id=alliance_id
    )

    if not corporations.exists():
        return None, None

    # Check access
    visible = models.CorporationAudit.objects.visible_to(request.user)

    # Check if there is an intersection between main_corp and visible
    common_corps = corporations.intersection(visible)
    if not common_corps.exists():
        perms = False

    ally = EveAllianceInfo.objects.get(alliance_id=alliance_id)
    return perms, ally


def get_all_corporations_from_alliance(
    request, alliance_id
) -> tuple[bool | None, list[models.CorporationAudit] | None]:
    """Get Alliance and check permissions for each corporation"""
    perms = True

    corporations = models.CorporationAudit.objects.filter(
        corporation__alliance__alliance_id=alliance_id
    )

    if not corporations.exists():
        return None, None

    # Check access
    visible = models.CorporationAudit.objects.visible_to(request.user)

    # Check if there is an intersection between main_corp and visible
    common_corps = corporations.intersection(visible)
    if not common_corps.exists():
        perms = False
    return perms, corporations


def get_alts_queryset(
    character: models.CharacterAudit,
) -> QuerySet[list[models.CharacterAudit]]:
    """Get all alts for a main character."""
    try:
        linked_characters = (
            character.eve_character.character_ownership.user.character_ownerships.all()
        )

        linked_characters = linked_characters.values_list("character_id", flat=True)
        return models.CharacterAudit.objects.filter(
            eve_character__id__in=linked_characters
        )
    except ObjectDoesNotExist:
        return models.CharacterAudit.objects.filter(
            eve_character__pk=character.eve_character.pk
        )
