from ninja import NinjaAPI

from django.db.models import Q

from ledger.api import schema
from ledger.api.helpers import get_alts_queryset, get_character
from ledger.hooks import get_extension_logger
from ledger.models.planetary import CharacterPlanet, CharacterPlanetDetails

logger = get_extension_logger(__name__)


class LedgerPlanetaryApiEndpoints:
    tags = ["CharacterPlanet"]

    def __init__(self, api: NinjaAPI):

        @api.get(
            "character/{character_id}/planetary/{planet_id}/",
            response={200: list[schema.CharacterPlanet], 403: str},
            tags=self.tags,
        )
        def get_planetary(request, character_id: int, planet_id: int):
            perm, main = get_character(request, character_id)

            if not perm:
                return 403, "Permission Denied"

            if character_id == 0:
                characters = get_alts_queryset(main)
            else:
                characters = [main]

            filters = Q(character__character__in=characters)
            if not planet_id == 0:
                filters &= Q(planet__id=planet_id)

            planets = CharacterPlanet.objects.filter(filters).select_related(
                "planet", "character"
            )

            output = []

            for p in planets:
                output.append(
                    {
                        "character_id": p.character.character.character_id,
                        "character_name": p.character.character.character_name,
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
            request_main = request.GET.get("main", False)
            perm, main = get_character(request, character_id)

            if not perm:
                return 403, "Permission Denied"

            if character_id == 0 or request_main:
                characters = get_alts_queryset(main)
            else:
                characters = [main]

            filters = Q(planet__character__character__in=characters)
            if not planet_id == 0:
                filters &= Q(planet__planet__id=planet_id)

            planets = (
                CharacterPlanetDetails.objects.filter(filters)
                .prefetch_related(
                    "planet",
                    "planet__planet",
                    "planet__character",
                    "planet__character__character",
                )
                .select_related("planet__planet")
            )

            output = []

            for p in planets:
                products_types = p.allocate_products()
                extracts = p.allocate_extracts()
                extractors = p.get_extractors_info()
                facility = p.get_facility_info()

                products = {
                    "raw": extracts,
                    "processed": products_types,
                }

                output.append(
                    {
                        "character_id": p.planet.character.character.character_id,
                        "character_name": p.planet.character.character.character_name,
                        "planet": p.planet.planet.name,
                        "planet_id": p.planet.planet.id,
                        "planet_type_id": p.planet.planet.eve_type.id,
                        "upgrade_level": p.planet.upgrade_level,
                        "expiry_date": p.get_planet_expiry_date(),
                        "expired": p.is_expired(),
                        "alarm": p.notification,
                        "extractors": extractors,
                        "products": products,
                        "storage": p.get_storage_info(),
                        "facility": facility,
                        "last_update": p.planet.last_update,
                    }
                )
            return output
