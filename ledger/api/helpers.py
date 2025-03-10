from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from allianceauth.eveonline.models import EveCharacter

from ledger import app_settings, models
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


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

    # check access
    visible = models.CharacterAudit.objects.visible_eve_characters(request.user)
    if main_char not in visible:
        perms = False
    return perms, main_char


def get_corporation(
    request, corporation_id
) -> tuple[bool | None, list[models.CorporationAudit] | None]:
    """Get Corporation and check permissions for each corporation"""
    perms = True
    if corporation_id == 0:
        corporations = get_main_and_alts_ids_corporations(request)
    else:
        corporations = [corporation_id]

    main_corp = models.CorporationAudit.objects.filter(
        corporation__corporation_id__in=corporations
    )

    if not main_corp.exists():
        return None, None

    # Check access
    visible = models.CorporationAudit.objects.visible_to(request.user)
    # Check if there is an intersection between main_corp and visible
    common_corps = main_corp.intersection(visible)
    if not common_corps.exists():
        perms = False
    return perms, main_corp.values_list("corporation__corporation_id", flat=True)


def get_alliance(
    request, alliance_id
) -> tuple[bool | None, list[models.CorporationAudit] | None]:
    """Get Alliance and check permissions for each corporation"""
    perms = True
    if alliance_id == 0:
        alliances = get_main_and_alts_ids_alliances(request)
    else:
        alliances = [alliance_id]

    main_ally = models.CorporationAudit.objects.filter(
        corporation__alliance__alliance_id__in=alliances
    )

    if not main_ally.exists():
        return None, None

    # Check access
    visible = models.CorporationAudit.objects.visible_to(request.user)

    # Check if there is an intersection between main_corp and visible
    common_corps = main_ally.intersection(visible)
    if not common_corps.exists():
        perms = False
    return perms, main_ally.values_list("corporation__alliance__alliance_id", flat=True)


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


def get_corp_alts_queryset(
    main_char, corporations=None
) -> list[models.general.EveEntity]:
    """Get all alts for a main character, optionally filtered by corporations."""
    try:
        linked_characters = (
            main_char.character_ownership.user.character_ownerships.all()
        )
        chars_list = set()

        if corporations:
            linked_characters = linked_characters.filter(
                character__corporation_id__in=corporations
            )

        for char in linked_characters:
            char, _ = models.general.EveEntity.objects.get_or_create(
                eve_id=char.character.character_id,
                defaults={
                    "name": char.character.character_name,
                    "category": "character",
                },
            )
            chars_list.add(char.eve_id)
        return list(models.general.EveEntity.objects.filter(eve_id__in=chars_list))
    except ObjectDoesNotExist:
        chars = EveCharacter.objects.filter(pk=main_char.pk).values("character_id")
        return list(models.general.EveEntity.objects.filter(eve_id__in=chars))


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


def get_main_and_alts_ids_corporations(request) -> set:
    """Get all corporation ids for main and alts."""
    linked_characters = request.user.profile.main_character.character_ownership.user.character_ownerships.select_related(
        "character", "user"
    ).all()

    linked_characters = linked_characters.values_list("character_id", flat=True)
    corp_ids = EveCharacter.objects.filter(id__in=linked_characters).values_list(
        "corporation_id", flat=True
    )

    return set(corp_ids)


def get_main_and_alts_ids_alliances(request) -> set:
    """Get all alliance ids for main and alts."""
    linked_characters = request.user.profile.main_character.character_ownership.user.character_ownerships.select_related(
        "character", "user"
    ).all()

    linked_characters = linked_characters.values_list("character_id", flat=True)
    ally_ids = EveCharacter.objects.filter(id__in=linked_characters).values_list(
        "alliance_id", flat=True
    )

    return set(ally_ids)
