# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.exceptions import HTTPNotModified

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EvePlanet, EveType

# AA Ledger
from ledger import __title__
from ledger.app_settings import LEDGER_BULK_BATCH_SIZE
from ledger.decorators import log_timing
from ledger.models.characteraudit import CharacterOwner
from ledger.models.helpers.update_manager import CharacterUpdateSection
from ledger.providers import esi

if TYPE_CHECKING:  # pragma: no cover
    # Alliance Auth
    from esi.stubs import CharactersCharacterIdPlanetsGetItem as PlanetGetItem
    from esi.stubs import CharactersCharacterIdPlanetsPlanetIdGet as PlanetDetailsItem

    # AA Ledger
    from ledger.models.general import UpdateSectionResult
    from ledger.models.planetary import CharacterPlanet as PlanetContext
    from ledger.models.planetary import CharacterPlanetDetails as PlanetDetailsContext

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def to_json_serializable(data):
    if isinstance(data, dict):
        return {k: to_json_serializable(v) for k, v in data.items()}
    if isinstance(data, list):
        return [to_json_serializable(i) for i in data]
    if hasattr(data, "__dict__"):
        return to_json_serializable(data.__dict__)
    if isinstance(data, timezone.datetime):
        return data.isoformat()
    return data


class CharacterPlanetManager(models.Manager["PlanetContext"]):
    @log_timing(logger)
    def update_or_create_esi(
        self, owner: CharacterOwner, force_refresh: bool = False
    ) -> "UpdateSectionResult":
        """Update or Create a planets entry from ESI data."""
        return owner.update_manager.update_section_if_changed(
            section=CharacterUpdateSection.PLANETS,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(
        self, owner: CharacterOwner, force_refresh: bool = False
    ) -> None:
        """Fetch planetary entries from ESI data."""
        req_scopes = ["esi-planets.manage_planets.v1"]
        token = owner.get_token(scopes=req_scopes)

        # Make the ESI request
        operation = esi.client.Planetary_Interaction.GetCharactersCharacterIdPlanets(
            character_id=owner.eve_character.character_id,
            token=token,
        )

        planets_items = operation.results(force_refresh=force_refresh)

        self._update_or_create_objs(owner=owner, objs=planets_items)

    @transaction.atomic()
    def _update_or_create_objs(
        self, owner: CharacterOwner, objs: list["PlanetGetItem"]
    ) -> None:
        """Update or Create planets entries from objs data."""
        # pylint: disable=import-outside-toplevel
        # AA Ledger
        from ledger.models.planetary import CharacterPlanetDetails

        _current_planets = self.filter(character=owner).values_list(
            "eve_planet_id", flat=True
        )

        _planets_ids = []
        _planets_new = []
        _planets_update = []

        for planet in objs:
            eve_planet, _ = EvePlanet.objects.get_or_create_esi(id=planet.planet_id)
            _planets_ids.append(eve_planet.id)

            try:
                e_planet = self.get(character=owner, eve_planet=eve_planet)
                prim_key = e_planet.id
            except self.model.DoesNotExist:
                prim_key = None

            planet = self.model(
                id=prim_key,
                name=eve_planet.name,
                character=owner,
                eve_planet=eve_planet,
                upgrade_level=planet.upgrade_level,
                num_pins=planet.num_pins,
            )

            if eve_planet.id not in _current_planets:
                _planets_new.append(planet)
            else:
                _planets_update.append(planet)

        if _planets_new:
            self.bulk_create(_planets_new, batch_size=LEDGER_BULK_BATCH_SIZE)
        if _planets_update:
            self.bulk_update(
                _planets_update,
                fields=["upgrade_level", "num_pins"],
                batch_size=LEDGER_BULK_BATCH_SIZE,
            )

        # Delete Planets that are no longer in the list
        obsolete_planets = set(_current_planets) - set(_planets_ids)
        self.filter(character=owner, eve_planet_id__in=obsolete_planets).delete()
        # Delete Planet Details that are no longer in the list
        CharacterPlanetDetails.objects.filter(
            planet__character=owner, planet__eve_planet_id__in=obsolete_planets
        ).delete()


class PlanetDetailsQuerySet(models.QuerySet):
    def update_or_create_layout(
        self,
        owner: CharacterOwner,
        planet: "PlanetDetailsContext",
        objs: list["PlanetDetailsItem"],
    ):
        """Update or Create Layout for a given Planet"""
        return self._update_or_create(owner=owner, planet=planet, objs=objs)

    def _convert_to_dict(
        self,
        result: list,
    ) -> tuple:
        objects_list = []
        for data in result:
            data_dict = to_json_serializable(data)
            objects_list.append(data_dict)
        return objects_list

    def _update_or_create(
        self,
        owner: CharacterOwner,
        planet: "PlanetDetailsContext",
        objs: list["PlanetDetailsItem"],
    ) -> tuple["PlanetDetailsContext", bool]:
        """Update or Create Layout for a given Planet"""
        if not isinstance(objs, list):
            objs = [objs]

        for result in objs:
            links = self._convert_to_dict(result.links)
            pins = self._convert_to_dict(result.pins)
            routes = self._convert_to_dict(result.routes)

            planetdetails, created = self.update_or_create(
                planet=planet,
                character=owner,
                defaults={
                    "links": links,
                    "pins": pins,
                    "routes": routes,
                    "factories": None,
                },
            )

            self._update_factory(planetdetails)

            logger.debug("Planet %s Factories Updated", planetdetails)

            return planetdetails, created

    def _update_factory(self, planet: "PlanetDetailsContext"):

        factory_dict = {}

        # Process pins
        for pin in planet.pins:
            pin_id = pin["pin_id"]
            item_type, _ = EveType.objects.get_or_create_esi(id=pin["type_id"])

            # Skip Command Center
            if pin["type_id"] in EveType.objects.filter(eve_group_id=1027).values_list(
                "id", flat=True
            ):
                continue

            # Create Facility Pin Entry
            factory_dict[pin_id] = {
                "facility_id": pin["type_id"],
                "facility_name": item_type.name,
                "facility_type": (
                    item_type.eve_group.name if item_type.eve_group else "N/A"
                ),
                "ressources": [],
            }

            # Spaceport and Storage Facility
            if pin["type_id"] in EveType.objects.filter(
                eve_group_id__in=[1029, 1030]
            ).values_list("id", flat=True):
                factory_dict[pin_id]["storage"] = {}
                self._storage_info(pin, factory_dict[pin_id])

            # Extractor
            if pin["type_id"] in EveType.objects.filter(eve_group_id=1063).values_list(
                "id", flat=True
            ):
                factory_dict[pin_id]["extractor"] = {}
                self._extractor_info(pin, factory_dict[pin_id])

        self._factory_production_chain(planet, factory_dict)

        planet.factories = factory_dict
        planet.save()
        return planet

    def _storage_info(self, pin: dict, facility_dict: dict):
        """Update per-facility dict and add all Storage Information."""
        for content in pin.get("contents", []):
            item_type, _ = EveType.objects.get_or_create_esi(id=content["type_id"])

            item_type_id = content["type_id"]
            item_amount = content["amount"]

            if item_type_id in facility_dict["storage"]:
                facility_dict["storage"][item_type_id]["amount"] += item_amount
            else:
                facility_dict["storage"][item_type_id] = {
                    "item_id": item_type_id,
                    "item_name": item_type.name,
                    "amount": item_amount,
                }
        return facility_dict

    def _extractor_info(self, pin: dict, factory_dict: dict):
        """Update dict and add all Extractor Information to the given dict"""
        # Update Extractor Information (ensure None is treated as empty dict)
        extractor_details = pin.get("extractor_details") or {}
        product_type_id = extractor_details.get("product_type_id")
        product_type_name = "N/A"

        # Get Product Eve Type
        if product_type_id:
            item_type, _ = EveType.objects.get_or_create_esi(id=product_type_id)
            product_type_name = item_type.name

        # Use timezone-aware datetimes and compute elapsed/total seconds
        current_time = timezone.now()

        install_time = None
        if pin.get("install_time") is not None:
            install_time = parse_datetime(pin.get("install_time"))
        expiry_time = None
        if pin.get("expiry_time") is not None:
            expiry_time = parse_datetime(pin.get("expiry_time"))

        # Create Extractor Info Entry on the per-facility dict
        factory_dict["extractor"] = {
            "head_count": extractor_details.get("head_count"),
            "product_type_id": product_type_id,
            "product_type_name": product_type_name,
            "install_time": str(install_time),
            "expiry_time": str(expiry_time),
            "cycle_time": extractor_details.get("cycle_time"),
            "progress_percentage": None,
        }

        is_running = False
        # Calculate progress as percentage (0-100) based on elapsed time
        if install_time and expiry_time:
            total_seconds = (expiry_time - install_time).total_seconds()
            if total_seconds > 0:
                elapsed_seconds = (current_time - install_time).total_seconds()
                progress = (elapsed_seconds / total_seconds) * 100.0
                progress = max(0.0, min(progress, 100.0))
                factory_dict["extractor"]["progress_percentage"] = round(progress, 2)

            # Extractor is running
            if progress < 100.0:
                is_running = True

        # Store is_running status
        factory_dict["extractor"]["is_running"] = is_running

    # pylint: disable=too-many-locals
    def _factory_production_chain(
        self, planet: "PlanetDetailsContext", factory_dict: dict
    ):
        """Update dict and add all Production Information to the given dict"""
        item_ids = set()
        for facility in factory_dict.values():
            for storage_item in facility.get("storage", {}).values():
                item_ids.add(storage_item["item_id"])

            extractor_product = facility.get("extractor", {}).get("product_type_id")
            if extractor_product:
                item_ids.add(extractor_product)

        for route in planet.routes:
            destination_pin_id = route["destination_pin_id"]
            source_pin_id = route["source_pin_id"]
            content_type, _ = EveType.objects.get_or_create_esi(
                id=route["content_type_id"]
            )

            if destination_pin_id in factory_dict:
                req_quantity = route["quantity"]
                storage = factory_dict[destination_pin_id].get("storage", {})
                current_quantity = storage.get(content_type.id, {}).get("amount", 0)
                missing_quantity = max((req_quantity - current_quantity), 0)

                still_producing = (
                    content_type.id in item_ids if not planet.is_expired else False
                )

                is_active = still_producing and missing_quantity > 0

                resource = {
                    "item_id": content_type.id,
                    "item_name": content_type.name,
                    "req_quantity": req_quantity,
                    "current_quantity": current_quantity,
                    "missing_quantity": missing_quantity,
                    "is_active": is_active,
                }
                factory_dict[destination_pin_id]["ressources"].append(resource)

            if source_pin_id in factory_dict:
                factory_dict[source_pin_id]["output_product"] = {
                    "item_id": content_type.id,
                    "item_name": content_type.name,
                    "output_quantity": route["quantity"],
                }
        return factory_dict


class PlanetDetailsManager(models.Manager["PlanetDetailsContext"]):
    def get_queryset(self):
        return PlanetDetailsQuerySet(self.model, using=self._db)

    @log_timing(logger)
    def update_or_create_esi(
        self, owner: CharacterOwner, force_refresh: bool = False
    ) -> "UpdateSectionResult":
        """Update or Create a planets details entry from ESI data."""
        return owner.update_manager.update_section_if_changed(
            section=CharacterUpdateSection.PLANETS_DETAILS,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(
        self, owner: CharacterOwner, force_refresh: bool = False
    ) -> None:
        """Fetch planets details entries from ESI data."""
        # pylint: disable=import-outside-toplevel
        # AA Ledger
        from ledger.models.planetary import CharacterPlanet

        req_scopes = ["esi-planets.manage_planets.v1"]

        token = owner.get_token(scopes=req_scopes)

        planets_ids = CharacterPlanet.objects.filter(character=owner).values_list(
            "eve_planet_id", flat=True
        )
        is_updated = False

        for planet_id in planets_ids:
            # Make the ESI request
            operation = esi.client.Planetary_Interaction.GetCharactersCharacterIdPlanetsPlanetId(
                character_id=owner.eve_character.character_id,
                planet_id=planet_id,
                token=token,
            )

            try:
                planets_details_items = operation.results(force_refresh=force_refresh)
                is_updated = True
            except HTTPNotModified:
                continue

            self._update_or_create_objs(
                owner=owner,
                objs=planets_details_items,
                planet_id=planet_id,
            )
        # Raise if no update happened at all
        if not is_updated:
            raise HTTPNotModified(304, {"msg": "Planets Details has Not Modified"})

    @transaction.atomic()
    def _update_or_create_objs(
        self,
        owner: CharacterOwner,
        objs: list["PlanetDetailsItem"],
        planet_id: int,
    ) -> None:
        """Update or Create planets entries from objs data."""
        # pylint: disable=import-outside-toplevel
        # AA Ledger
        from ledger.models.planetary import CharacterPlanet

        try:
            character_planet = CharacterPlanet.objects.get(
                character=owner, eve_planet_id=planet_id
            )
        except CharacterPlanet.DoesNotExist:
            logger.warning(
                "Planet %s not found for character %s",
                planet_id,
                owner.eve_character.character_name,
            )
            return

        planet_details, created = self.get_queryset().update_or_create_layout(
            owner=owner,
            planet=character_planet,
            objs=objs,
        )

        if not created:
            # Set Alert if Extractor Heads are expired
            if planet_details.is_expired and planet_details.last_alert is None:
                logger.debug(
                    "Planet %s Extractor Heads Expired for: %s",
                    planet_details.planet.eve_planet.name,
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
                    planet_details.planet.eve_planet.name,
                )
                planet_details.last_alert = None
                planet_details.notification_sent = False

            planet_details.save()
