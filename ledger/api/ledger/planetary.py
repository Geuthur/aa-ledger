# Third Party
from ninja import NinjaAPI

# Django
from django.db.models import Q
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.api import schema
from ledger.api.api_helper.planetary_helper import (
    generate_progressbar,
    get_facilities_info,
)
from ledger.api.helpers import get_alts_queryset, get_character_or_none
from ledger.models.planetary import CharacterPlanet, CharacterPlanetDetails

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class LedgerPlanetaryApiEndpoints:
    tags = ["CharacterPlanet"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "character/{character_id}/planetary/{planet_id}/",
            response={200: list[schema.CharacterPlanet], 403: str},
            tags=self.tags,
        )
        def get_planetary(request, character_id: int, planet_id: int):
            is_all = False
            if character_id == 0:
                character_id = request.user.profile.main_character.character_id
                is_all = True

            perm, character = get_character_or_none(request, character_id)

            if not perm:
                return 403, str(_("Permission Denied"))

            if is_all:
                characters = get_alts_queryset(character)
            else:
                characters = [character]

            filters = Q(character__eve_character__in=characters)
            if not planet_id == 0:
                filters &= Q(planet__id=planet_id)

            planets = CharacterPlanet.objects.filter(filters).select_related(
                "planet", "character"
            )

            output = []

            for p in planets:
                output.append(
                    {
                        "character_id": p.character.eve_character.character_id,
                        "character_name": p.character.eve_character.character_name,
                        "planet": p.planet.name,
                        "planet_id": p.planet.id,
                        "upgrade_level": p.upgrade_level,
                        "num_pins": p.num_pins,
                        "last_update": p.last_update,
                    }
                )
            return output

        @api.get(
            "character/{character_id}/planetary/{planet_id}/details/",
            response={200: list, 403: str},
            tags=self.tags,
        )
        # pylint: disable=too-many-locals
        def get_planetarydetails(request, character_id: int, planet_id: int):
            singleview = request.GET.get("single", False)
            perm, character = get_character_or_none(request, character_id)

            if not perm:
                return 403, str(_("Permission Denied"))

            if not singleview:
                characters = get_alts_queryset(character)
            else:
                characters = [character]

            filters = Q(planet__character__in=characters)
            if not planet_id == 0:
                filters &= Q(planet__planet__id=planet_id)

            planets = (
                CharacterPlanetDetails.objects.filter(filters)
                .prefetch_related(
                    "planet",
                    "planet__planet",
                    "planet__character",
                )
                .select_related("planet__planet")
            )

            output = []

            for p in planets:
                products_types = p.allocate_products()
                extracts = p.allocate_extracts()

                products = {
                    "raw": extracts,
                    "processed": products_types,
                }

                output.append(
                    {
                        "character_id": p.planet.character.eve_character.character_id,
                        "character_name": p.planet.character.eve_character.character_name,
                        "planet": p.planet.planet.name,
                        "planet_id": p.planet.planet.id,
                        "planet_type_id": p.planet.planet.eve_type.id,
                        "upgrade_level": p.planet.upgrade_level,
                        "expiry_date": p.get_planet_expiry_date(),
                        "expired": p.is_expired,
                        "alarm": p.notification,
                        "percentage": generate_progressbar(
                            p.allocate_overall_progress()
                        ),
                        "products": products,
                        "storage": p.get_storage_info(),
                        "facility": p.facilitys,
                        "last_update": p.planet.last_update,
                    }
                )
            return output

        @api.get(
            "character/{character_id}/planetary/{planet_id}/factory/",
            response={200: dict, 403: str},
            tags=self.tags,
        )
        def get_factory_info(request, character_id: int, planet_id: int):
            # Get the character
            perm, character = get_character_or_none(request, character_id)

            if not perm:
                return 403, str(_("Permission Denied"))

            filters = Q(planet__character=character)
            if planet_id != 0:
                filters &= Q(planet__planet__id=planet_id)

            try:
                planet = CharacterPlanetDetails.objects.get(filters)
                storage = planet.get_storage_info()
                facilities = get_facilities_info(planet)

                output = {
                    "title": _("Factory Information"),
                    "character_id": planet.planet.character.eve_character.character_id,
                    "character_name": planet.planet.character.eve_character.character_name,
                    "planet_id": planet.planet.planet.id,
                    "planet_name": planet.planet.planet.name,
                    "facilities": facilities,
                    "storage": storage,
                    "last_update": planet.planet.last_update,
                }
            except CharacterPlanetDetails.DoesNotExist:
                output = {
                    "title": _("Planet not Found"),
                }

            context = {
                "character": output,
                "mode": "factory",
            }

            return render(
                request,
                "ledger/partials/modal/view_factory.html",
                context,
            )

        @api.get(
            "character/{character_id}/planetary/{planet_id}/extractor/",
            response={200: dict, 403: str},
            tags=self.tags,
        )
        def get_extractor_info(request, character_id: int, planet_id: int):
            perm, character = get_character_or_none(request, character_id)

            if not perm:
                return 403, str(_("Permission Denied"))

            filters = Q(planet__character=character)
            if not planet_id == 0:
                filters &= Q(planet__planet__id=planet_id)

            try:
                planet = CharacterPlanetDetails.objects.get(filters)
                output = {
                    "title": _("Extractor Information"),
                    "character_id": planet.planet.character.eve_character.character_id,
                    "character_name": planet.planet.character.eve_character.character_name,
                    "planet_id": planet.planet.planet.id,
                    "planet_name": planet.planet.planet.name,
                    "extractors": planet.get_extractors_info(),
                    "last_update": planet.planet.last_update,
                }
            except CharacterPlanetDetails.DoesNotExist:
                output = {
                    "title": _("Planet not Found"),
                }
                return output

            context = {
                "character": output,
                "mode": "extractor",
            }

            return render(
                request,
                "ledger/partials/modal/view_extractor.html",
                context,
            )
