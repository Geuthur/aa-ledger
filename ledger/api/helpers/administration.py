"""Administration API Helpers and Data Builders."""

# Standard Library
from typing import Any

# Django
from django.db.models import Count, F, Max, Q
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)

# AA Ledger
from ledger.api import schema
from ledger.api.helpers.core import _build_sections, _character_icon
from ledger.helpers.eveonline import (
    get_alliance_logo_url,
    get_corporation_logo_url,
)
from ledger.models.characteraudit import CharacterOwner
from ledger.models.corporationaudit import CorporationOwner
from ledger.models.helpers.update_manager import (
    CharacterUpdateSection,
    CorporationUpdateSection,
)


def build_administration_character_owners(
    user: Any,
) -> list[schema.AdministrationOwnerSchema]:
    """Build owner schemas for characters manageable by the user."""
    char_owners = (
        CharacterOwner.objects.manage_to(user)
        .filter(
            Q(
                eve_character=F(
                    "eve_character__character_ownership__user__profile__main_character"
                )
            )
            | Q(eve_character__character_ownership__isnull=True)
        )
        .select_related(
            "eve_character",
            "eve_character__character_ownership",
            "eve_character__character_ownership__user",
        )
        .prefetch_related(
            "ledger_update_status",
            "eve_character__character_ownership__user__character_ownerships__character",
        )
        .annotate_total_update_status()
        .annotate(last_sync=Max("ledger_update_status__last_run_finished_at"))
        .order_by("eve_character__character_name")
    )

    owners_list: list[schema.AdministrationOwnerSchema] = []
    for char_owner in char_owners:
        eve_char = char_owner.eve_character
        user_id = None
        user_name = None
        alts: list[schema.AltSchema] = []

        if hasattr(eve_char, "character_ownership") and eve_char.character_ownership:
            user_id = eve_char.character_ownership.user_id
            user_name = eve_char.character_ownership.user.username
            alts = [
                schema.AltSchema(
                    character_id=co.character.character_id,
                    character_name=co.character.character_name,
                    icon=_character_icon(
                        co.character.character_id, co.character.character_name
                    ),
                    ticker=co.character.corporation_ticker,
                )
                for co in eve_char.character_ownership.user.character_ownerships.all()
            ]

        error_message = _build_sections(
            char_owner.ledger_update_status.all(), CharacterUpdateSection
        )[1]

        owners_list.append(
            schema.AdministrationOwnerSchema(
                id=char_owner.id,
                owner_id=eve_char.character_id,
                owner_type="character",
                name=eve_char.character_name,
                icon=_character_icon(eve_char.character_id, eve_char.character_name),
                ticker=eve_char.corporation_ticker,
                user_id=user_id,
                user_name=user_name,
                status=char_owner.get_status,
                is_active=char_owner.active,
                last_sync=char_owner.last_sync,
                error_message=error_message,
                alts=alts,
            )
        )
    return owners_list


def build_administration_corporation_owners(
    user: Any,
) -> tuple[list[schema.AdministrationOwnerSchema], list[CorporationOwner]]:
    """Build owner schemas for corporations manageable by the user."""
    corp_owners = list(
        CorporationOwner.objects.manage_to(user)
        .select_related("eve_corporation", "eve_corporation__alliance")
        .prefetch_related("ledger_corporation_update_status")
        .annotate_total_update_status()
        .annotate(
            last_sync=Max("ledger_corporation_update_status__last_run_finished_at")
        )
        .order_by("eve_corporation__corporation_name")
    )

    corp_ids = [c.eve_corporation.corporation_id for c in corp_owners]
    registered_char_ids = CharacterOwner.objects.filter(
        eve_character__corporation_id__in=corp_ids
    ).values_list("eve_character__character_id", flat=True)

    corp_unregistered_counts = dict(
        EveCharacter.objects.filter(corporation_id__in=corp_ids)
        .exclude(character_id__in=registered_char_ids)
        .values("corporation_id")
        .annotate(total=Count("character_id"))
        .values_list("corporation_id", "total")
    )

    owners_list: list[schema.AdministrationOwnerSchema] = []
    for corp_owner in corp_owners:
        eve_corp = corp_owner.eve_corporation
        error_message = _build_sections(
            corp_owner.ledger_corporation_update_status.all(),
            CorporationUpdateSection,
        )[1]

        owners_list.append(
            schema.AdministrationOwnerSchema(
                id=corp_owner.id,
                owner_id=eve_corp.corporation_id,
                owner_type="corporation",
                name=eve_corp.corporation_name,
                icon=get_corporation_logo_url(
                    corporation_id=eve_corp.corporation_id,
                    corporation_name=eve_corp.corporation_name,
                    size=64,
                ),
                ticker=eve_corp.corporation_ticker,
                user_id=None,
                user_name=None,
                status=corp_owner.get_status,
                is_active=corp_owner.active,
                last_sync=corp_owner.last_sync,
                error_message=error_message,
                unregistered_count=corp_unregistered_counts.get(
                    eve_corp.corporation_id, 0
                ),
            )
        )
    return owners_list, corp_owners


def build_administration_alliance_owners(
    corp_owners: list[CorporationOwner],
) -> list[schema.AdministrationOwnerSchema]:
    """Build owner schemas for alliances visible to the user (only alliances with a corporation in audit)."""
    all_alliance_ids = {
        corp.eve_corporation.alliance.alliance_id
        for corp in corp_owners
        if corp.eve_corporation and corp.eve_corporation.alliance
    }

    if not all_alliance_ids:
        return []

    alliance_registered_corps = set(
        CorporationOwner.objects.filter(
            eve_corporation__alliance__alliance_id__in=all_alliance_ids
        ).values_list("eve_corporation__corporation_id", flat=True)
    )
    alliance_unregistered_counts = dict(
        EveCorporationInfo.objects.filter(alliance__alliance_id__in=all_alliance_ids)
        .exclude(corporation_id__in=alliance_registered_corps)
        .values("alliance__alliance_id")
        .annotate(total=Count("corporation_id"))
        .values_list("alliance__alliance_id", "total")
    )

    alliance_last_sync = {}
    for corp in corp_owners:
        if corp.eve_corporation and corp.eve_corporation.alliance:
            ally_id = corp.eve_corporation.alliance.alliance_id
            sync_val = getattr(corp, "last_sync", None)
            if sync_val:
                if ally_id not in alliance_last_sync or str(sync_val) > str(
                    alliance_last_sync[ally_id]
                ):
                    alliance_last_sync[ally_id] = sync_val

    alliances = EveAllianceInfo.objects.filter(
        alliance_id__in=all_alliance_ids
    ).order_by("alliance_name")

    owners_list: list[schema.AdministrationOwnerSchema] = []
    for alliance in alliances:
        owners_list.append(
            schema.AdministrationOwnerSchema(
                id=alliance.alliance_id,
                owner_id=alliance.alliance_id,
                owner_type="alliance",
                name=alliance.alliance_name,
                icon=get_alliance_logo_url(alliance.alliance_id, 64),
                ticker=alliance.alliance_ticker,
                user_id=None,
                user_name=None,
                status="ok",
                is_active=True,
                last_sync=alliance_last_sync.get(alliance.alliance_id),
                error_message=None,
                unregistered_count=alliance_unregistered_counts.get(
                    alliance.alliance_id, 0
                ),
            )
        )
    return owners_list


def build_administration_owners_list(
    user: Any,
) -> list[schema.AdministrationOwnerSchema]:
    """Return unified list of character, corporation, and alliance owners for administration."""
    char_owners = build_administration_character_owners(user)
    corp_owners, raw_corp_owners = build_administration_corporation_owners(user)
    alliance_owners = build_administration_alliance_owners(raw_corp_owners)

    return [*char_owners, *corp_owners, *alliance_owners]
