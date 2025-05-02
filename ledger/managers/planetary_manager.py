# Standard Library
import logging
from typing import TYPE_CHECKING

# Django
from django.db import models
from django.utils import timezone

# Alliance Auth (External Libs)
from eveuniverse.models import EveType

# AA Ledger
from ledger.constants import COMMAND_CENTER, EXTRACTOR_CONTROL_UNIT, SPACEPORTS

if TYPE_CHECKING:  # pragma: no cover
    # AA Ledger
    from ledger.models.planetary import CharacterPlanet, CharacterPlanetDetails

logger = logging.getLogger(__name__)


class PlanetaryQuerySet(models.QuerySet):
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
        self, planet: "CharacterPlanetDetails", esi_result: dict
    ):
        """Update or Create Layout for a given Planet"""
        return self._update_or_create(planet=planet, esi_result=esi_result)

    def _update_or_create(self, planet: "CharacterPlanetDetails", esi_result: dict):
        planetdetails, created = self.update_or_create(
            planet=planet,
            defaults={
                "links": esi_result["links"],
                "pins": esi_result["pins"],
                "routes": esi_result["routes"],
                "facilitys": None,
                "last_update": timezone.now(),
            },
        )

        self._update_facility(planetdetails)

        logger.debug("Planet %s Facilitys Updated", planetdetails)

        return planetdetails, created

    def _update_facility(self, planet: "CharacterPlanetDetails"):
        facility_info = self.get_facility_info(planet)
        logger.debug("Facility Info: %s", facility_info)
        planet.facilitys = facility_info
        planet.save()
        logger.debug("Planet %s saved with updated facilitys", planet)
        logger.debug("Facilitys: %s", planet.facilitys)
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


class PlanetaryManagerBase(models.Manager):
    pass


PlanetaryManager = PlanetaryManagerBase.from_queryset(PlanetaryQuerySet)
