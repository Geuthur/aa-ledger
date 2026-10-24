# Django
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet, Sum
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo, EveCharacter
from allianceauth.services.hooks import get_extension_logger
from esi.models import Token

# AA Ledger
from ledger import __title__, models
from ledger.api import schema
from ledger.helpers.eveonline import get_character_portrait_url
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


def get_available_years(journal: QuerySet) -> list[int]:
    """Return the years with journal entries, newest first (current year if none)."""
    years = list(
        journal.values_list("date__year", flat=True).order_by("-date__year").distinct()
    )
    return years or [timezone.now().year]


def get_characterowner_or_none(
    request, character_id
) -> tuple[bool, models.CharacterOwner | None]:
    """Get Character and check permissions"""
    perms = True

    try:
        owner = models.CharacterOwner.objects.get(
            eve_character__character_id=character_id
        )
    except ObjectDoesNotExist:
        return False, None
    except ValueError:
        return None, None

    # check access
    visible = models.CharacterOwner.objects.visible_eve_characters(request.user)
    if owner.eve_character not in visible:
        perms = False
    return perms, owner


def get_corporationowner_or_none(
    request, corporation_id
) -> tuple[bool | None, models.CorporationOwner | None]:
    """Return Corporation and check permissions"""
    perms = True

    try:
        main_corp = models.CorporationOwner.objects.get(
            eve_corporation__corporation_id=corporation_id
        )
    except ObjectDoesNotExist:
        return None, None

    # Check access
    visible = models.CorporationOwner.objects.visible_to(request.user)
    if main_corp not in visible:
        perms = False
    return perms, main_corp


def get_manage_corporation(
    request, corporation_id
) -> tuple[bool | None, models.CorporationOwner | None]:
    """Returns a tuple of the permissions and the corporation object if manageable"""
    perms = True

    try:
        main_corp = models.CorporationOwner.objects.get(
            eve_corporation__corporation_id=corporation_id
        )
    except ObjectDoesNotExist:
        return None, None

    # Check access
    visible = models.CorporationOwner.objects.manage_to(request.user)
    if main_corp not in visible:
        perms = False
    return perms, main_corp


def get_alliance_or_none(
    request, alliance_id
) -> tuple[bool | None, EveAllianceInfo | None]:
    """Get Alliance and check permissions for each corporation"""
    perms = True

    corporations = models.CorporationOwner.objects.filter(
        eve_corporation__alliance__alliance_id=alliance_id
    )

    if not corporations.exists():
        return None, None

    # Check access
    visible = models.CorporationOwner.objects.visible_to(request.user)

    # Check if there is an intersection between main_corp and visible
    common_corps = corporations.intersection(visible)
    if not common_corps.exists():
        perms = False

    ally = EveAllianceInfo.objects.get(alliance_id=alliance_id)
    return perms, ally


def get_all_corporations_from_alliance(
    request, alliance_id
) -> tuple[bool | None, list[models.CorporationOwner] | None]:
    """Get Alliance and check permissions for each corporation"""
    perms = True

    corporations = models.CorporationOwner.objects.filter(
        eve_corporation__alliance__alliance_id=alliance_id
    )

    if not corporations.exists():
        return None, None

    # Check access
    visible = models.CorporationOwner.objects.visible_to(request.user)

    # Check if there is an intersection between main_corp and visible
    common_corps = corporations.intersection(visible)
    if not common_corps.exists():
        perms = False
    return perms, corporations


def get_alts_queryset(
    owner: models.CharacterOwner,
) -> QuerySet[list[models.CharacterOwner]]:
    """Get all alts for a main character."""
    try:
        linked_characters = (
            owner.eve_character.character_ownership.user.character_ownerships.all()
        )

        linked_characters = linked_characters.values_list("character_id", flat=True)
        return models.CharacterOwner.objects.filter(
            eve_character__id__in=linked_characters
        )
    except ObjectDoesNotExist:
        return models.CharacterOwner.objects.filter(
            eve_character__pk=owner.eve_character.pk
        )


def _character_icon(character_id: int, character_name: str) -> str:
    return get_character_portrait_url(
        character_id=character_id, character_name=character_name, size=64
    )


def _build_sections(
    update_statuses, section_choices_class
) -> tuple[list[schema.AdminOwnerSectionSchema], str | None]:
    status_map = {s.section: s for s in update_statuses}
    section_list: list[schema.AdminOwnerSectionSchema] = []
    latest_error: str | None = None
    for sec in section_choices_class:
        st_obj = status_map.get(sec.value)
        if st_obj:
            if st_obj.error_message and not latest_error:
                latest_error = st_obj.error_message
            section_list.append(
                schema.AdminOwnerSectionSchema(
                    section=sec.value,
                    section_name=str(sec.label),
                    is_success=st_obj.is_success,
                    has_token_error=st_obj.has_token_error,
                    error_message=st_obj.error_message or None,
                    last_run_at=st_obj.last_run_at,
                    last_run_finished_at=st_obj.last_run_finished_at,
                )
            )
        else:
            section_list.append(
                schema.AdminOwnerSectionSchema(
                    section=sec.value,
                    section_name=str(sec.label),
                    is_success=None,
                    has_token_error=False,
                    error_message=None,
                    last_run_at=None,
                    last_run_finished_at=None,
                )
            )
    return section_list, latest_error


def get_user_added_corporation_ids(user) -> list[int]:
    """Return list of corporation IDs the user has personally added or owns."""
    if not user.is_authenticated:
        return []

    # Corps where user has an ESI token with corp audit scopes
    corp_scoped_chars = (
        Token.objects.filter(user=user)
        .require_scopes(models.CorporationOwner.get_esi_scopes())
        .values_list("character_id", flat=True)
    )
    corp_ids = set(
        EveCharacter.objects.filter(character_id__in=corp_scoped_chars).values_list(
            "corporation_id", flat=True
        )
    )

    # Corps where user has owned characters with tokens
    user_token_chars = Token.objects.filter(user=user).values_list(
        "character_id", flat=True
    )
    owned_corps = user.character_ownerships.filter(
        character__character_id__in=user_token_chars
    ).values_list("character__corporation_id", flat=True)
    corp_ids.update(owned_corps)

    return list(corp_ids)


def get_user_issue_count(user) -> int:
    """
    Return the number of failed update sections of the user's own characters
    and of the corporations the user has personally added (as shown in Settings).
    """
    characters = (
        models.CharacterOwner.objects.annotate_total_update_status_user(user=user)
        .aggregate(total_failed=Sum("num_sections_failed"))
        .get("total_failed")
    ) or 0
    corporations = (
        models.CorporationOwner.objects.filter(
            eve_corporation__corporation_id__in=get_user_added_corporation_ids(user)
        )
        .annotate_total_update_status()
        .aggregate(total_failed=Sum("num_sections_failed"))
        .get("total_failed")
    ) or 0
    return characters + corporations
