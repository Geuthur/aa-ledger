# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.api import schema
from ledger.models.characteraudit import CharacterOwner
from ledger.models.corporationaudit import CorporationOwner
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
