# Standard Library
from datetime import datetime

# Django
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, QuerySet

# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo, EveCharacter
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__, models

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def get_character(request, character_id) -> tuple[bool, EveCharacter | None]:
    """Get Character and check permissions"""
    perms = True

    try:
        character = EveCharacter.objects.get(character_id=character_id)
    except ObjectDoesNotExist:
        return False, None
    except ValueError:
        return None, None

    # check access
    visible = models.CharacterAudit.objects.visible_eve_characters(request.user)
    if character not in visible:
        perms = False
    return perms, character


def get_corporation(
    request, corporation_id
) -> tuple[bool | None, models.CorporationAudit | None]:
    """Get Corporation and check permissions for each corporation"""
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


def get_alts_queryset(main_char) -> QuerySet[list[EveCharacter]]:
    """Get all alts for a main character."""
    try:
        linked_characters = (
            main_char.character_ownership.user.character_ownerships.all()
        )

        linked_characters = linked_characters.values_list("character_id", flat=True)

        return EveCharacter.objects.filter(id__in=linked_characters)
    except ObjectDoesNotExist:
        return EveCharacter.objects.filter(pk=main_char.pk)


def get_journal_entitys(date: datetime, view, corporations=None) -> set:
    """Get all entity ids from Corporation Journal Queryset filtered by date."""
    filter_date = Q(date__year=date.year)
    if view == "month":
        filter_date &= Q(date__month=date.month)
    elif view == "day":
        filter_date &= Q(date__month=date.month)
        filter_date &= Q(date__day=date.day)

    first_party_ids = models.CorporationWalletJournalEntry.objects.filter(
        filter_date,
        division__corporation__corporation__corporation_id__in=corporations,
    ).values_list("first_party_id", flat=True)

    second_party_ids = models.CorporationWalletJournalEntry.objects.filter(
        filter_date, division__corporation__corporation__corporation_id__in=corporations
    ).values_list("second_party_id", flat=True)

    entity_ids = set(first_party_ids) | set(second_party_ids)

    return entity_ids
