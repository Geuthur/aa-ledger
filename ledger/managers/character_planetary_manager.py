# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.utils import timezone

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EvePlanet, EveType

# AA Ledger
from ledger import __title__
from ledger.constants import COMMAND_CENTER, EXTRACTOR_CONTROL_UNIT, SPACEPORTS
from ledger.decorators import log_timing
from ledger.helpers.etag import etag_results
from ledger.models.characteraudit import CharacterAudit
from ledger.providers import esi

if TYPE_CHECKING:  # pragma: no cover
    # AA Ledger
    from ledger.models.general import UpdateSectionResult
    from ledger.models.planetary import CharacterPlanet, CharacterPlanetDetails

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def convert_datetime_to_str(data):
    if isinstance(data, dict):
        return {k: convert_datetime_to_str(v) for k, v in data.items()}
    if isinstance(data, list):
        return [convert_datetime_to_str(i) for i in data]
    if isinstance(data, timezone.datetime):
        return data.isoformat()
    return data


class PlanetaryQuerySet(models.QuerySet):
    pass


class PlanetaryManagerBase(models.Manager):
    @log_timing(logger)
    def update_or_create_esi(
        self, character: "CharacterAudit", force_refresh: bool = False
    ) -> "UpdateSectionResult":
        """Update or Create a planets entry from ESI data."""
        return character.update_section_if_changed(
            section=character.UpdateSection.PLANETS,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(
        self, character: "CharacterAudit", force_refresh: bool = False
    ) -> None:
        """Fetch planetary entries from ESI data."""
        req_scopes = ["esi-planets.manage_planets.v1"]

        token = character.get_token(scopes=req_scopes)
        planets_obj = (
            esi.client.Planetary_Interaction.get_characters_character_id_planets(
                character_id=character.eve_character.character_id
            )
        )
        planets_items = etag_results(planets_obj, token, force_refresh=force_refresh)
        self._update_or_create_objs(character, planets_items)

    @transaction.atomic()
    def _update_or_create_objs(self, character: "CharacterAudit", objs: list) -> None:
        """Update or Create planets entries from objs data."""
        # pylint: disable=import-outside-toplevel
        # AA Ledger
        from ledger.models.planetary import CharacterPlanetDetails

        _current_planets = self.filter(character=character).values_list(
            "planet_id", flat=True
        )

        _planets_ids = []
        _planets_new = []
        _planets_update = []

        for planet in objs:
            eve_planet, _ = EvePlanet.objects.get_or_create_esi(id=planet["planet_id"])
            _planets_ids.append(eve_planet.id)

            try:
                e_planet = self.get(character=character, planet=eve_planet)
                prim_key = e_planet.id
            except self.model.DoesNotExist:
                prim_key = None

            planet = self.model(
                id=prim_key,
                character=character,
                planet=eve_planet,
                planet_name=eve_planet.name,
                upgrade_level=planet["upgrade_level"],
                num_pins=planet["num_pins"],
            )

            if eve_planet.id not in _current_planets:
                _planets_new.append(planet)
            else:
                _planets_update.append(planet)

        if _planets_new:
            self.bulk_create(_planets_new)
        if _planets_update:
            self.bulk_update(_planets_update, fields=["upgrade_level", "num_pins"])

        # Delete Planets that are no longer in the list
        obsolete_planets = set(_current_planets) - set(_planets_ids)
        self.filter(character=character, planet_id__in=obsolete_planets).delete()
        # Delete Planet Details that are no longer in the list
        CharacterPlanetDetails.objects.filter(
            planet__character=character, planet__planet_id__in=obsolete_planets
        ).delete()


PlanetaryManager = PlanetaryManagerBase.from_queryset(PlanetaryQuerySet)


class PlanetaryDetailsQuerySet(models.QuerySet):
    def get_or_create_facilitys(self, planet: "CharacterPlanet"):
        """Get or Create Facilitys for a given Planet"""
        return self._get_or_create_facilitys(planet=planet)

    def _get_or_create_facilitys(self, planet: "CharacterPlanet"):
        try:
            facilitys = self.get(planet=planet)
            facility = facilitys.facilitys
            created = False
            return facility, created
        except self.model.DoesNotExist:
            facility, created = self.update_or_create_facilitys(planet=planet)
        return facility, created

    def update_or_create_layout(
        self,
        character: CharacterAudit,
        planet: "CharacterPlanetDetails",
        esi_result: dict,
    ):
        """Update or Create Layout for a given Planet"""
        return self._update_or_create(
            character=character, planet=planet, esi_result=esi_result
        )

    def _update_or_create(
        self,
        character: "CharacterAudit",
        planet: "CharacterPlanetDetails",
        esi_result: dict,
    ):
        planetdetails, created = self.update_or_create(
            planet=planet,
            character=character,
            defaults={
                "links": esi_result["links"],
                "pins": esi_result["pins"],
                "routes": esi_result["routes"],
                "facilitys": None,
            },
        )

        self._update_facility(planetdetails)

        logger.debug("Planet %s Facilitys Updated", planetdetails)

        return planetdetails, created

    def _update_facility(self, planet: "CharacterPlanetDetails"):
        facility_info = self.get_facility_info(planet)
        planet.facilitys = facility_info
        planet.save()
        return planet

    # TODO make code easier or split it to peaces for better readable
    def get_facility_info(self, planet: "CharacterPlanetDetails"):
        facility_info = {}

        # Process pins
        for pin in planet.pins:
            pin_id = pin["pin_id"]
            item_type, _ = EveType.objects.get_or_create_esi(id=pin["type_id"])
            if (
                pin["type_id"] in SPACEPORTS
                or pin["type_id"] in EXTRACTOR_CONTROL_UNIT
                or pin["type_id"] in COMMAND_CENTER
            ):
                continue
            facility_info[pin_id] = {
                "facility_id": item_type.id,
                "facility_name": item_type.name,
                "resources": [],
                "storage": {
                    content["type_id"]: content["amount"]
                    for content in pin.get("contents", [])
                },
            }

        self._facility_production_chain(planet, facility_info)

        self._facility_produce_depend(planet, facility_info)

        return facility_info

    def _facility_production_chain(
        self, planet: "CharacterPlanetDetails", facility_info: dict
    ):
        """Update dict and add all Production Information to the given dict"""

        extractors = planet.get_extractors_info()
        extractors_item_ids = [
            extractor["item_id"] for extractor in extractors.values()
        ]

        for route in planet.routes:
            destination_pin_id = route["destination_pin_id"]
            source_pin_id = route["source_pin_id"]
            content_type, _ = EveType.objects.get_or_create_esi(
                id=route["content_type_id"]
            )

            if destination_pin_id in facility_info:
                req_quantity = route["quantity"]
                current_quantity = facility_info[destination_pin_id]["storage"].get(
                    content_type.id, 0
                )
                missing_quantity = req_quantity - current_quantity
                still_producing = (
                    content_type.id in extractors_item_ids
                    if not planet.is_expired
                    else False
                )

                resource = {
                    "item_id": content_type.id,
                    "item_name": content_type.name,
                    "req_quantity": req_quantity,
                    "current_quantity": current_quantity,
                    "missing_quantity": max(missing_quantity, 0),
                    "still_producing": still_producing,
                }
                facility_info[destination_pin_id]["resources"].append(resource)

            if source_pin_id in facility_info:
                facility_info[source_pin_id]["output_product"] = {
                    "item_id": content_type.id,
                    "item_name": content_type.name,
                    "output_quantity": route["quantity"],
                }
        return facility_info

    def _facility_produce_depend(self, planet, facility_info):
        """Check if Facility is Producing"""
        for facility in facility_info.values():
            for resource in facility["resources"]:
                self._facility_still_producing(planet, resource, facility_info)
        return facility_info

    def _facility_still_producing(self, planet, resource, facility_info) -> bool:
        """Check if ressource exist in Production Chain and change State"""
        for other_facility in facility_info.values():
            if (
                "output_product" in other_facility
                and other_facility["output_product"]["item_id"] == resource["item_id"]
                and not planet.is_expired
            ):
                if other_facility["output_product"]["output_quantity"] > 0:
                    resource["still_producing"] = True


class PlanetaryDetailsManagerBase(models.Manager):
    @log_timing(logger)
    def update_or_create_esi(
        self, character: "CharacterAudit", force_refresh: bool = False
    ) -> "UpdateSectionResult":
        """Update or Create a planets details entry from ESI data."""
        return character.update_section_if_changed(
            section=character.UpdateSection.PLANETS_DETAILS,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(
        self, character: "CharacterAudit", force_refresh: bool = False
    ) -> None:
        """Fetch planets details entries from ESI data."""
        # pylint: disable=import-outside-toplevel
        # AA Ledger
        from ledger.models.planetary import CharacterPlanet

        req_scopes = ["esi-planets.manage_planets.v1"]

        token = character.get_token(scopes=req_scopes)

        planets_ids = CharacterPlanet.objects.filter(character=character).values_list(
            "planet_id", flat=True
        )

        for planet_id in planets_ids:
            planets_obj = esi.client.Planetary_Interaction.get_characters_character_id_planets_planet_id(
                character_id=character.eve_character.character_id, planet_id=planet_id
            )
            planets_items = etag_results(
                planets_obj, token, force_refresh=force_refresh
            )
            self._update_or_create_objs(character, planets_items, planet_id=planet_id)

    @transaction.atomic()
    def _update_or_create_objs(
        self, character: "CharacterAudit", objs: list, planet_id: int
    ) -> None:
        """Update or Create planets entries from objs data."""
        # pylint: disable=import-outside-toplevel
        # AA Ledger
        from ledger.models.planetary import CharacterPlanet

        try:
            character_planet = CharacterPlanet.objects.get(
                character=character, planet_id=planet_id
            )
        except CharacterPlanet.DoesNotExist:
            logger.warning(
                "Planet %s not found for character %s",
                planet_id,
                character.eve_character.character_name,
            )
            return

        # Convert Time to string
        planet_details_items = convert_datetime_to_str(objs)

        planet_details, created = self.update_or_create_layout(
            character=character,
            planet=character_planet,
            esi_result=planet_details_items,
        )

        if not created:
            # Set Alert if Extractor Heads are expired
            if planet_details.is_expired and planet_details.last_alert is None:
                logger.debug(
                    "Planet %s Extractor Heads Expired for: %s",
                    planet_details.planet.planet.name,
                    planet_details.planet.character.eve_character.character_name,
                )
                planet_details.last_alert = timezone.now()

            # Reset Alert after 1 day
            if (
                planet_details.last_alert is not None
                and planet_details.last_alert
                < timezone.now() - timezone.timedelta(days=1)
            ):
                logger.debug(
                    "Notification Reseted for %s Planet: %s",
                    planet_details.planet.character.eve_character.character_name,
                    planet_details.planet.planet.name,
                )
                planet_details.last_alert = None
                planet_details.notification_sent = False

            planet_details.save()


PlanetaryDetailsManager = PlanetaryDetailsManagerBase.from_queryset(
    PlanetaryDetailsQuerySet
)
