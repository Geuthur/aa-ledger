# Third Party
from ninja import NinjaAPI, schema

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.api.api_helper.icons import (
    get_extractor_info_button,
    get_factory_info_button,
    get_toggle_notification_button,
)
from ledger.api.api_helper.planetary_helper import (
    FactorySchema,
    ProduceSchema,
    StorageSchema,
    allocate_overall_progress,
    generate_is_active_icon,
    generate_is_notification_icon,
    generate_progressbar,
    get_character_render_url,
    get_factories_info,
    get_factory_info,
    get_icon_render_url,
    get_storage_info,
    get_type_render_url,
)
from ledger.api.helpers import get_alts_queryset, get_characterowner_or_none
from ledger.api.schema import (
    EveTypeSchema,
    ExtractorSchema,
    OwnerSchema,
    PlanetSchema,
    ProgressBarSchema,
)
from ledger.models.planetary import CharacterPlanetDetails
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class FactoryDetailsResponse(schema.Schema):
    owner: OwnerSchema
    planet: PlanetSchema
    factories: list[ProduceSchema]
    storage: list[StorageSchema]


class ExtractorDetailsResponse(schema.Schema):
    owner: OwnerSchema
    planet: PlanetSchema
    extractors: list[ExtractorSchema]


class PlanetaryDetailsActions(schema.Schema):
    factory_info_button: str
    extractor_info_button: str
    toggle_notification_button: str


class PlanetaryDetails(schema.Schema):
    owner: OwnerSchema
    planet: PlanetSchema
    expired: str | bool
    alarm: str | bool
    progress_bar: str
    factories: list[FactorySchema]
    actions: PlanetaryDetailsActions


class PlanetaryApiEndpoints:
    tags = ["CharacterPlanet"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "character/{character_id}/planet/{planet_id}/details/",
            response={200: list[PlanetaryDetails], 403: str},
            tags=self.tags,
        )
        # pylint: disable=too-many-locals
        def get_planetarydetails(
            request: WSGIRequest, character_id: int, planet_id: int
        ):
            singleview = request.GET.get("single", False)
            perm, character = get_characterowner_or_none(request, character_id)

            if not perm:
                return 403, str(_("Permission Denied"))

            if not singleview:
                characters = get_alts_queryset(character)
            else:
                characters = [character]

            filters = Q(planet__character__in=characters)
            if not planet_id == 0:
                filters &= Q(planet__id=planet_id)

            planets_details = CharacterPlanetDetails.objects.filter(filters)
            response_planetary_details_list: list[PlanetaryDetails] = []

            for details in planets_details:
                response_factories_list = get_factories_info(planet_details=details)

                response_planetary_details = PlanetaryDetails(
                    owner=OwnerSchema(
                        character_id=details.planet.character.eve_character.character_id,
                        character_name=details.planet.character.eve_character.character_name,
                        icon=get_character_render_url(
                            character_id=details.planet.character.eve_character.character_id,
                            character_name=details.planet.character.eve_character.character_name,
                            as_html=True,
                        ),
                    ),
                    planet=PlanetSchema(
                        id=details.planet.eve_planet.id,
                        name=details.planet.eve_planet.name,
                        type=EveTypeSchema(
                            id=details.planet.eve_planet.eve_type.id,
                            name=details.planet.eve_planet.eve_type.name,
                            icon=get_icon_render_url(
                                type_id=details.planet.eve_planet.eve_type.id,
                                type_name=details.planet.eve_planet.eve_type.name,
                                size=32,
                                as_html=True,
                            ),
                        ),
                        upgrade_level=details.planet.upgrade_level,
                        num_pins=details.planet.num_pins,
                        last_update=details.planet.last_update,
                    ),
                    factories=response_factories_list,
                    expired=generate_is_active_icon(
                        is_active=not details.is_expired,
                    ),
                    alarm=generate_is_notification_icon(
                        is_notification=details.notification
                    ),
                    progress_bar=generate_progressbar(
                        allocate_overall_progress(details)
                    ),
                    actions=PlanetaryDetailsActions(
                        factory_info_button=get_factory_info_button(
                            planet_details=details
                        ),
                        extractor_info_button=get_extractor_info_button(
                            planet_details=details
                        ),
                        toggle_notification_button=get_toggle_notification_button(
                            planet_details=details
                        ),
                    ),
                )
                response_planetary_details_list.append(response_planetary_details)
            return response_planetary_details_list

        @api.get(
            "character/{character_id}/planet/{planet_id}/factory/",
            response={200: FactoryDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_factory_details(
            request: WSGIRequest, character_id: int, planet_id: int
        ):
            """
            Get Factory Information for a character's planet.

            Args:
                request (WSGIRequest): The HTTP request object.
                character_id (int): The ID of the character.
                planet_id (int): The ID of the planet.
            Returns:
                dict: Factory details including owner, planet info, factories, and storage.
            """
            perm, character = get_characterowner_or_none(request, character_id)

            if not perm:
                return 403, {"error": _("Permission Denied.")}

            filters = Q(planet__character=character)
            if planet_id != 0:
                filters &= Q(planet__id=planet_id)

            planet_details = CharacterPlanetDetails.objects.filter(filters).first()

            if not planet_details:
                return 403, {"error": _("Planet not found.")}

            response_storage_list = get_storage_info(planet_details=planet_details)
            response_factories_list = get_factory_info(planet_details=planet_details)

            return FactoryDetailsResponse(
                owner=OwnerSchema(
                    character_id=planet_details.planet.character.eve_character.character_id,
                    character_name=planet_details.planet.character.eve_character.character_name,
                ),
                planet=PlanetSchema(
                    id=planet_details.planet.eve_planet.id,
                    name=planet_details.planet.eve_planet.name,
                    type=EveTypeSchema(
                        id=planet_details.planet.eve_planet.eve_type.id,
                        name=planet_details.planet.eve_planet.eve_type.name,
                        icon=get_type_render_url(
                            type_id=planet_details.planet.eve_planet.eve_type.id,
                            size=32,
                            as_html=True,
                        ),
                    ),
                    upgrade_level=planet_details.planet.upgrade_level,
                    num_pins=planet_details.planet.num_pins,
                    last_update=planet_details.planet.last_update,
                ),
                factories=response_factories_list,
                storage=response_storage_list,
            )

        @api.get(
            "character/{character_id}/planet/{planet_id}/extractor/",
            response={200: ExtractorDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_extractor_details(
            request: WSGIRequest, character_id: int, planet_id: int
        ):
            """
            Get Extractor Information for a character's planet.

            Args:
                request (WSGIRequest): The HTTP request object.
                character_id (int): The ID of the character.
                planet_id (int): The ID of the planet.
            Returns:
                dict: Extractor details including owner, planet info, extractors, and last update.
            """
            perm, character = get_characterowner_or_none(request, character_id)

            if not perm:
                return 403, {"error": _("Permission Denied.")}

            filters = Q(planet__character=character)
            if not planet_id == 0:
                filters &= Q(planet__id=planet_id)

            planet_details = CharacterPlanetDetails.objects.filter(filters).first()

            if not planet_details:
                return 404, {"error": _("Planet not found.")}

            response_extractors: list[ExtractorSchema] = []

            if planet_details.factories:
                for factory in planet_details.factories.values():
                    extractor_info = factory.get("extractor", None)

                    # Skip if no extractor info
                    if not extractor_info:
                        continue

                    extractor = ExtractorSchema(
                        item_id=extractor_info["product_type_id"],
                        item_name=extractor_info["product_type_name"],
                        icon=get_icon_render_url(
                            type_id=extractor_info["product_type_id"],
                            type_name=extractor_info["product_type_name"],
                            as_html=True,
                        ),
                        install_time=extractor_info["install_time"],
                        expiry_time=extractor_info["expiry_time"],
                        progress=ProgressBarSchema(
                            percentage=str(extractor_info["progress_percentage"]),
                            html=generate_progressbar(
                                extractor_info["progress_percentage"]
                            ),
                        ),
                    )
                    response_extractors.append(extractor)

            return ExtractorDetailsResponse(
                owner=OwnerSchema(
                    character_id=planet_details.planet.character.eve_character.character_id,
                    character_name=planet_details.planet.character.eve_character.character_name,
                ),
                planet=PlanetSchema(
                    id=planet_details.planet.eve_planet.id,
                    name=planet_details.planet.eve_planet.name,
                    type=EveTypeSchema(
                        id=planet_details.planet.eve_planet.eve_type.id,
                        name=planet_details.planet.eve_planet.eve_type.name,
                        icon=get_type_render_url(
                            type_id=planet_details.planet.eve_planet.eve_type.id,
                            size=32,
                            as_html=True,
                        ),
                    ),
                    upgrade_level=planet_details.planet.upgrade_level,
                    num_pins=planet_details.planet.num_pins,
                    last_update=planet_details.planet.last_update,
                ),
                extractors=response_extractors,
            )

        @api.post(
            "character/{character_id}/planet/{planet_id}/toggle/",
            response={200: dict, 403: dict, 404: dict},
            tags=self.tags,
        )
        def toggle_planet_notification(
            request: WSGIRequest, character_id: int, planet_id: int
        ):
            """
            Toggle Notification for a character's planet.

            This endpoint toggles the notification setting for a character's planet.
            It validates the user's permission and the existence of the planet before performing the toggle action.

            Args:
                request (WSGIRequest): The HTTP request object.
                character_id (int): The ID of the character.
                planet_id (int): The ID of the planet.
            Returns:
                dict: A dictionary containing the success status and message.
            """
            perm, character = get_characterowner_or_none(request, character_id)

            if not perm:
                return 403, {"error": _("Permission Denied.")}

            filters = Q(planet__character=character)
            if not planet_id == 0:
                filters &= Q(planet__id=planet_id)

            planets = CharacterPlanetDetails.objects.filter(filters)

            if not planets.exists():
                return 404, {"error": _("Planet not found.")}

            on_count = planets.filter(notification=True).count()
            off_count = planets.filter(notification=False).count()
            majority_state = on_count > off_count

            for planet in planets:
                planet.notification = not majority_state
                planet.save()
            msg = _("Notification toggled successfully.")
            return {"success": True, "message": msg}
