import logging
from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from allianceauth.eveonline.models import EveAllianceInfo, EveCharacter

from ledger import app_settings, models

logger = logging.getLogger(__name__)


# TODO Handle it from generate_ledger
def convert_corp_tax(amount: Decimal) -> Decimal:
    """Convert corp tax to correct amount for character ledger"""
    return (amount / app_settings.LEDGER_CORP_TAX) * (
        100 - app_settings.LEDGER_CORP_TAX
    )


def get_character(
    request, character_id, corp=False
) -> tuple[bool, EveCharacter | None]:
    """Get Character and check permissions"""
    perms = True
    if character_id == 0:
        character_id = request.user.profile.main_character.character_id

    try:
        # Corporation View
        if corp:
            main_char = EveCharacter.objects.select_related(
                "character_ownership",
                "character_ownership__user__profile",
                "character_ownership__user__profile__main_character",
            ).get(character_id=request.user.profile.main_character.character_id)
        else:
            main_char = EveCharacter.objects.get(character_id=character_id)
    except ObjectDoesNotExist:
        return False, None
    except ValueError:
        return None, None

    # check access
    visible = models.CharacterAudit.objects.visible_eve_characters(request.user)
    if main_char not in visible:
        perms = False
    return perms, main_char


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

    try:
        main_corp = models.CorporationAudit.objects.get(
            corporation__alliance__alliance_id=alliance_id
        )
        ally = main_corp.corporation.alliance
    except ObjectDoesNotExist:
        return None, None

    # Check access
    visible = models.CorporationAudit.objects.visible_to(request.user)
    if main_corp not in visible:
        perms = False
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


def get_alts_queryset(main_char, corporations=None) -> list[EveCharacter]:
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
