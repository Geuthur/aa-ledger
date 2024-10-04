"""
Planetary Model
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from eveuniverse.models import EvePlanet, EveType

from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import CharacterAudit

logger = get_extension_logger(__name__)


class CharacterPlanet(models.Model):

    id = models.AutoField(primary_key=True)

    character = models.ForeignKey(
        CharacterAudit, on_delete=models.CASCADE, related_name="ledger_characterplanet"
    )

    upgrade_level = models.IntegerField(
        default=0, help_text=_("Upgrade level of the planet")
    )

    num_pins = models.IntegerField(
        default=0, help_text=_("Number of pins on the planet")
    )

    planet = models.ForeignKey(
        EvePlanet, on_delete=models.CASCADE, related_name="ledger_planet"
    )

    last_update = models.DateTimeField(null=True, default=None, blank=True)

    # objects = AuditCharacterManager()

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

    # objects = AuditCharacterManager()

    class Meta:
        default_permissions = ()
        indexes = [
            models.Index(fields=["planet"]),
        ]

    def __str__(self):
        return f"Planet Details Data: {self.planet.character.character.character_name} - {self.planet.planet.name}"

    def count_extractors(self):
        return len([pin for pin in self.pins if pin.get("type_id") == 3060])

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
        product_types = {}
        for c_type_id in self.routes:
            type_id = c_type_id.get("content_type_id")
            if type_id and type_id not in product_types:
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
        valid_type_ids = [2256, 2542, 2543, 2544, 2552, 2555, 2556, 2557]
        for pin in self.pins:
            if pin.get("type_id") in valid_type_ids:
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
