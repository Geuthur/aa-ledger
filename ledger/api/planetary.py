# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI, Query, schema

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.api.helpers.core import get_alts_queryset, get_characterowner_or_none
from ledger.api.helpers.planetary_helper import (
    ProduceSchema,
    StorageSchema,
    allocate_overall_progress,
    get_factory_info,
    get_storage_info,
)
from ledger.api.schema import (
    ErrorSchema,
    EveTypeSchema,
    ExtractorSchema,
    MessageSchema,
    OwnerSchema,
    PlanetSchema,
    PlanetSelection,
)
from ledger.helpers.eveonline import (
    get_character_portrait_url,
    get_icon_render_url,
)
from ledger.models.planetary import CharacterPlanetDetails
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class PlanetaryDetails(schema.Schema):
    """A planet of a character. `id` is the identifier for the detail and notification endpoints."""

    id: int
    owner: OwnerSchema
    planet: PlanetSchema
    expired: bool
    alarm: bool
    progress: float | None = None
    factories: list[ProduceSchema]


class PlanetDetailResponse(schema.Schema):
    owner: OwnerSchema
    planet: PlanetSchema
    factories: list[ProduceSchema]
    storage: list[StorageSchema]
    extractors: list[ExtractorSchema]


class NotificationResponse(MessageSchema):
    notification: bool


def _planet_schema(details: CharacterPlanetDetails) -> PlanetSchema:
    eve_planet = details.planet.eve_planet
    return PlanetSchema(
        id=eve_planet.id,
        name=eve_planet.name,
        type=EveTypeSchema(
            id=eve_planet.item_type.id,
            name=eve_planet.item_type.name,
            icon=get_icon_render_url(type_id=eve_planet.item_type.id, size=64),
        ),
        upgrade_level=details.planet.upgrade_level,
        num_pins=details.planet.num_pins,
        last_update=details.planet.last_update,
    )


def _owner_schema(details: CharacterPlanetDetails) -> OwnerSchema:
    eve_character = details.planet.character.eve_character
    return OwnerSchema(
        character_id=eve_character.character_id,
        character_name=eve_character.character_name,
        icon=get_character_portrait_url(
            character_id=eve_character.character_id,
            character_name=eve_character.character_name,
        ),
    )


def _extractors(details: CharacterPlanetDetails) -> list[ExtractorSchema]:
    extractors: list[ExtractorSchema] = []
    for factory in (details.factories or {}).values():
        extractor_info = factory.get("extractor", None)
        if not extractor_info:
            continue
        extractors.append(
            ExtractorSchema(
                item_id=extractor_info["product_type_id"],
                item_name=extractor_info["product_type_name"],
                icon=get_icon_render_url(
                    type_id=extractor_info["product_type_id"],
                    type_name=extractor_info["product_type_name"],
                ),
                install_time=extractor_info["install_time"],
                expiry_time=extractor_info["expiry_time"],
                progress=float(extractor_info["progress_percentage"]),
            )
        )
    return extractors


class PlanetaryApiEndpoints:
    tags = ["CharacterPlanet"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "character/{character_id}/planets/",
            response={
                HTTPStatus.OK: list[PlanetaryDetails],
                HTTPStatus.FORBIDDEN: ErrorSchema,
                HTTPStatus.NOT_FOUND: ErrorSchema,
            },
            tags=self.tags,
            summary="Get the planets of a character, optionally including its alts",
        )
        def get_planetarydetails(
            request: WSGIRequest,
            character_id: int,
            filters: Query[PlanetSelection],
        ):
            perm, character = get_characterowner_or_none(request, character_id)

            if character is None:
                return HTTPStatus.NOT_FOUND, {"error": _("Character not found.")}
            if not perm:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            characters = get_alts_queryset(character)

            planets_details = filters.filter(
                CharacterPlanetDetails.objects.filter(planet__character__in=characters)
            ).select_related(
                "planet__character__eve_character",
                "planet__eve_planet__item_type",
            )

            return [
                PlanetaryDetails(
                    id=details.planet.id,
                    owner=_owner_schema(details),
                    planet=_planet_schema(details),
                    expired=details.is_expired,
                    alarm=details.notification,
                    progress=allocate_overall_progress(details),
                    factories=get_factory_info(planet_details=details),
                )
                for details in planets_details
            ]

        @api.get(
            "character/{character_id}/planets/{int:planet_id}/",
            response={
                HTTPStatus.OK: PlanetDetailResponse,
                HTTPStatus.FORBIDDEN: ErrorSchema,
                HTTPStatus.NOT_FOUND: ErrorSchema,
            },
            tags=self.tags,
            summary="Get factories, storage and extractors of a planet",
        )
        def get_planet_details(request: WSGIRequest, character_id: int, planet_id: int):
            perm, character = get_characterowner_or_none(request, character_id)

            if character is None:
                return HTTPStatus.NOT_FOUND, {"error": _("Character not found.")}
            if not perm:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            characters = get_alts_queryset(character)

            details = CharacterPlanetDetails.objects.filter(
                planet__character__in=characters, planet__id=planet_id
            ).first()

            if details is None:
                return HTTPStatus.NOT_FOUND, {"error": _("Planet not found.")}

            return PlanetDetailResponse(
                owner=_owner_schema(details),
                planet=_planet_schema(details),
                factories=get_factory_info(planet_details=details),
                storage=get_storage_info(planet_details=details),
                extractors=_extractors(details),
            )

        @api.post(
            "character/{character_id}/planets/notification/",
            response={
                HTTPStatus.OK: NotificationResponse,
                HTTPStatus.FORBIDDEN: ErrorSchema,
                HTTPStatus.NOT_FOUND: ErrorSchema,
            },
            tags=self.tags,
            summary="Toggle the expiry notification of one or all planets",
        )
        def toggle_planet_notification(
            request: WSGIRequest, character_id: int, selection: Query[PlanetSelection]
        ):
            perm, character = get_characterowner_or_none(request, character_id)

            if character is None:
                return HTTPStatus.NOT_FOUND, {"error": _("Character not found.")}
            if not perm:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            characters = get_alts_queryset(character)

            planets = selection.filter(
                CharacterPlanetDetails.objects.filter(planet__character__in=characters)
            )

            if not planets.exists():
                return HTTPStatus.NOT_FOUND, {"error": _("Planet not found.")}

            # If a single planet is targeted, invert its specific notification status
            if selection.planet_id is not None:
                single_planet = planets.first()
                notification = not single_planet.notification
                planets.update(notification=notification)
            else:
                # Switch all planets to the opposite of the current majority
                notification = not (
                    planets.filter(notification=True).count()
                    > planets.filter(notification=False).count()
                )
                planets.update(notification=notification)

            return NotificationResponse(
                message=_("Notification toggled successfully."),
                notification=notification,
            )
