# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.api import schema
from ledger.helpers.eveonline import (
    get_alliance_logo_url,
    get_character_portrait_url,
    get_corporation_logo_url,
)
from ledger.models.characteraudit import CharacterOwner
from ledger.models.corporationaudit import CorporationOwner
from ledger.models.general import General
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


def _main_character_overview(character_ids) -> list[schema.CharacterOverview]:
    """Return the main characters of all accounts owning the given characters."""
    profiles = (
        UserProfile.objects.filter(
            main_character__isnull=False,
            main_character__character_id__in=character_ids,
        )
        .select_related("main_character")
        .order_by("main_character__character_name")
    )
    return [
        schema.CharacterOverview(
            character_id=profile.main_character.character_id,
            character_name=profile.main_character.character_name,
            corporation_id=profile.main_character.corporation_id,
            corporation_name=profile.main_character.corporation_name,
        )
        for profile in profiles
    ]


class ApiEndpoints:
    tags = ["LedgerAdmin"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "overview/",
            response={
                HTTPStatus.OK: schema.LedgerOverviewResponse,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Get unified overview of all owners (characters, corporations, alliances) visible to user",
        )
        def get_overview(request: WSGIRequest):
            user = request.user
            if not General.has_perm(user, General.Permission.BASIC_ACCESS):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            owners: list[schema.LedgerOverviewOwnerSchema] = []

            # 1. Characters
            chars_ids = CharacterOwner.objects.visible_to(user).values_list(
                "eve_character__character_id", flat=True
            )
            planetary_char_ids = set(
                CharacterOwner.objects.visible_eve_characters(user).values_list(
                    "character_id", flat=True
                )
            )
            can_manage = General.has_perm(user, General.Permission.MANAGE_ACCESS)

            profiles = (
                UserProfile.objects.filter(
                    main_character__isnull=False,
                    main_character__character_id__in=chars_ids,
                )
                .select_related("main_character")
                .order_by("main_character__character_name")
            )
            char_error_ids = set(
                CharacterOwner.objects.filter(
                    ledger_update_status__is_success=False
                ).values_list("eve_character__character_id", flat=True)
            )

            for profile in profiles:
                char = profile.main_character
                owners.append(
                    schema.LedgerOverviewOwnerSchema(
                        id=char.character_id,
                        name=char.character_name,
                        type="character",
                        type_display=str(_("Character")),
                        portrait_url=get_character_portrait_url(char.character_id, 64),
                        subtitle=char.corporation_name,
                        active=True,
                        has_planetary=(char.character_id in planetary_char_ids),
                        can_manage=can_manage or (profile.user_id == user.id),
                        has_errors=(char.character_id in char_error_ids),
                    )
                )

            # 2. Corporations & Alliances
            if General.has_perm(user, General.Permission.ADVANCED_ACCESS):
                corps = (
                    CorporationOwner.objects.visible_to(user)
                    .select_related("eve_corporation", "eve_corporation__alliance")
                    .order_by("eve_corporation__corporation_name")
                )
                corp_error_ids = set(
                    CorporationOwner.objects.filter(
                        ledger_corporation_update_status__is_success=False
                    ).values_list("eve_corporation__corporation_id", flat=True)
                )
                alliances_dict = {}
                for corp in corps:
                    eve_corp = corp.eve_corporation
                    owners.append(
                        schema.LedgerOverviewOwnerSchema(
                            id=eve_corp.corporation_id,
                            name=eve_corp.corporation_name,
                            type="corporation",
                            type_display=str(_("Corporation")),
                            portrait_url=get_corporation_logo_url(
                                eve_corp.corporation_id, 64
                            ),
                            subtitle=(
                                eve_corp.alliance.alliance_name
                                if eve_corp.alliance
                                else None
                            ),
                            active=True,
                            has_planetary=False,
                            can_manage=can_manage,
                            has_errors=(eve_corp.corporation_id in corp_error_ids),
                        )
                    )
                    if eve_corp.alliance:
                        alliances_dict[eve_corp.alliance.alliance_id] = (
                            eve_corp.alliance
                        )

                for ally in sorted(
                    alliances_dict.values(), key=lambda a: a.alliance_name.lower()
                ):
                    owners.append(
                        schema.LedgerOverviewOwnerSchema(
                            id=ally.alliance_id,
                            name=ally.alliance_name,
                            type="alliance",
                            type_display=str(_("Alliance")),
                            portrait_url=get_alliance_logo_url(ally.alliance_id, 64),
                            subtitle=None,
                            active=True,
                            has_planetary=False,
                            can_manage=can_manage,
                        )
                    )

            return schema.LedgerOverviewResponse(owners=owners)

        @api.get(
            "character/overview/",
            response={HTTPStatus.OK: list[schema.CharacterOverview]},
            tags=self.tags,
            summary="Get all main characters visible to the user",
        )
        def get_character_overview(request: WSGIRequest):
            chars_ids = CharacterOwner.objects.visible_to(request.user).values_list(
                "eve_character__character_id", flat=True
            )
            return _main_character_overview(chars_ids)

        @api.get(
            "planetary/overview/",
            response={HTTPStatus.OK: list[schema.CharacterOverview]},
            tags=self.tags,
            summary="Get all main characters with planetary access",
        )
        def get_planetary_overview(request: WSGIRequest):
            chars_ids = CharacterOwner.objects.visible_eve_characters(
                request.user
            ).values_list("character_id", flat=True)
            return _main_character_overview(chars_ids)

        @api.get(
            "corporation/overview/",
            response={HTTPStatus.OK: list[schema.CorporationOverview]},
            tags=self.tags,
            summary="Get all corporations visible to the user",
        )
        def get_corporation_overview(request: WSGIRequest):
            corporations = CorporationOwner.objects.visible_to(
                request.user
            ).select_related("eve_corporation")
            return [
                schema.CorporationOverview(
                    corporation_id=corporation.eve_corporation.corporation_id,
                    corporation_name=corporation.eve_corporation.corporation_name,
                )
                for corporation in corporations
            ]

        @api.get(
            "alliance/overview/",
            response={HTTPStatus.OK: list[schema.AllianceOverview]},
            tags=self.tags,
            summary="Get all alliances visible to the user",
        )
        def get_alliance_overview(request: WSGIRequest):
            corporations = CorporationOwner.objects.visible_to(
                request.user
            ).select_related("eve_corporation__alliance")
            alliances = {
                corporation.eve_corporation.alliance.alliance_id: schema.AllianceOverview(
                    alliance_id=corporation.eve_corporation.alliance.alliance_id,
                    alliance_name=corporation.eve_corporation.alliance.alliance_name,
                )
                for corporation in corporations
                if corporation.eve_corporation.alliance is not None
            }
            return list(alliances.values())
