"""
Planetary Model
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from eveuniverse.models import EvePlanet, EveType

from ledger.constants.pi import (
    COMMAND_CENTER,
    EXTRACTOR_CONTROL_UNIT,
    P0_PRODUCTS,
    SPACEPORTS,
)
from ledger.hooks import get_extension_logger
from ledger.managers.planetary_manager import PlanetaryManager
from ledger.models.characteraudit import CharacterAudit

logger = get_extension_logger(__name__)


class CharacterPlanet(models.Model):
    id = models.AutoField(primary_key=True)

    planet_name = models.CharField(max_length=100, null=True, default=None)

    planet = models.ForeignKey(
        EvePlanet, on_delete=models.CASCADE, related_name="ledger_planet"
    )

    character = models.ForeignKey(
        CharacterAudit, on_delete=models.CASCADE, related_name="ledger_characterplanet"
    )

    upgrade_level = models.IntegerField(
        default=0, help_text=_("Upgrade level of the planet")
    )

    num_pins = models.IntegerField(
        default=0, help_text=_("Number of pins on the planet")
    )

    last_update = models.DateTimeField(null=True, default=None, blank=True)

    # objects = PlanetaryManager()

    class Meta:
        default_permissions = ()
        indexes = [
            models.Index(fields=["character"]),
            models.Index(fields=["planet"]),
        ]

    def __str__(self):
        return f"Planet Data: {self.character.character.character_name} - {self.planet.name}"

    @classmethod
    def get_esi_scopes(cls) -> list[str]:
        """Return list of required ESI scopes to fetch."""
        return [
            "esi-planets.manage_planets.v1",
        ]


class CharacterPlanetDetails(models.Model):
    id = models.AutoField(primary_key=True)

    planet = models.ForeignKey(
        CharacterPlanet,
        on_delete=models.CASCADE,
        related_name="ledger_characterplanetdetails",
    )

    links = models.JSONField(null=True, default=None, blank=True)
    pins = models.JSONField(null=True, default=None, blank=True)
    routes = models.JSONField(null=True, default=None, blank=True)

    last_update = models.DateTimeField(null=True, default=None, blank=True)
    last_alert = models.DateTimeField(null=True, default=None, blank=True)

    notification = models.BooleanField(default=False)
    notification_sent = models.BooleanField(default=False)

    objects = PlanetaryManager()

    class Meta:
        default_permissions = ()
        indexes = [
            models.Index(fields=["planet"]),
        ]

    def __str__(self):
        return f"Planet Details Data: {self.planet.character.character.character_name} - {self.planet.planet.name}"

    def count_extractors(self):
        return len(
            [pin for pin in self.pins if pin.get("type_id") in EXTRACTOR_CONTROL_UNIT]
        )

    def get_planet_install_date(self):
        install_times = [
            pin.get("install_time")
            for pin in self.pins
            if pin.get("install_time") and pin["install_time"] != "0"
        ]
        if install_times:
            install = timezone.datetime.fromisoformat(
                min(install_times).replace("Z", "+00:00")
            )
            return install
        return None

    def get_planet_expiry_date(self):
        expiry_times = [
            pin.get("expiry_time")
            for pin in self.pins
            if pin.get("expiry_time") and pin["expiry_time"] != "0"
        ]
        if expiry_times:
            alert = timezone.datetime.fromisoformat(
                min(expiry_times).replace("Z", "+00:00")
            )
            return alert
        return None

    def is_expired(self):
        expiry_date = self.get_planet_expiry_date()
        if expiry_date is None:
            return False
        return expiry_date < timezone.now()

    def get_types(self) -> list:
        """Get the product types of the routes on the planet"""
        types = []
        for pin in self.routes:
            if pin.get("content_type_id") not in types:
                types.append(pin.get("content_type_id"))
        return types

    def allocate_products(self) -> dict:
        """Get the product types on the planet"""
        product_types = {}
        for c_type_id in self.routes:
            type_id = c_type_id.get("content_type_id")
            if type_id not in P0_PRODUCTS and type_id not in product_types:
                type_data, _ = EveType.objects.get_or_create_esi(id=type_id)
                product_types[type_id] = {
                    "id": type_id,
                    "name": type_data.name,
                    "category": type_data.eve_group.name,
                }
        return product_types

    def allocate_extracts(self) -> dict:
        """Get the extractor raw product types on the planet"""
        product_types = {}
        for c_type_id in self.routes:
            type_id = c_type_id.get("content_type_id")
            if type_id in P0_PRODUCTS and type_id not in product_types:
                type_data, _ = EveType.objects.get_or_create_esi(id=type_id)
                product_types[type_id] = {
                    "id": type_id,
                    "name": type_data.name,
                    "category": type_data.eve_group.name,
                }
        return product_types

    def get_extractors_info(self) -> dict:
        extractors = {}
        for pin in self.pins:
            extractor_details = pin.get("extractor_details")
            if extractor_details and "cycle_time" in extractor_details:
                type_id = extractor_details.get("product_type_id")
                type_data, _ = EveType.objects.get_or_create_esi(id=type_id)
                extractors[pin.get("pin_id")] = {
                    "install_time": pin.get("install_time"),
                    "expiry_time": pin.get("expiry_time"),
                    "product_type_id": type_id,
                    "product_name": type_data.name,
                }
        return extractors

    def get_storage_info(self) -> dict:
        storage = {}
        for pin in self.pins:
            if pin.get("type_id") in SPACEPORTS:
                type_id = pin.get("type_id")
                type_data, _ = EveType.objects.get_or_create_esi(id=type_id)
                contents_info = []
                for content in pin.get("contents", []):
                    content_type_id = content.get("type_id")
                    content_type_data, _ = EveType.objects.get_or_create_esi(
                        id=content_type_id
                    )
                    contents_info.append(
                        {
                            "amount": content.get("amount"),
                            "type_id": content_type_id,
                            "product_name": content_type_data.name,
                        }
                    )
                storage[pin.get("pin_id")] = {
                    "product_type_id": type_id,
                    "product_name": type_data.name,
                    "contents": contents_info,
                }
        return storage

    def get_facility_info(self):
        facility_info = {}

        # Process pins
        for pin in self.pins:
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

        # Process routes
        for route in self.routes:
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
                resource = {
                    "item_id": content_type.id,
                    "item_name": content_type.name,
                    "req_quantity": req_quantity,
                    "current_quantity": current_quantity,
                    "missing_quantity": max(missing_quantity, 0),
                }
                facility_info[destination_pin_id]["resources"].append(resource)

            if source_pin_id in facility_info:
                facility_info[source_pin_id]["output_product"] = {
                    "item_id": content_type.id,
                    "item_name": content_type.name,
                    "output_quantity": route["quantity"],
                }

        return facility_info
