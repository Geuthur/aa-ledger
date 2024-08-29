"""
Planetary Model
"""

from typing import List

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

    balance = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, default=None
    )

    # objects = AuditCharacterManager()

    def __str__(self):
        return f"Planet Data: {self.character.character.character_name} - {self.planet.name}"

    @classmethod
    def get_esi_scopes(cls) -> List[str]:
        """Return list of required ESI scopes to fetch."""
        return [
            "esi-planets.manage_planets.v1",
        ]


class CharacterPlanetDetails(models.Model):
    _PRODUCTION_IDS = {
        "P0": [
            2286,
            2305,
            2267,
            2288,
            2287,
            2307,
            2272,
            2309,
            2073,
            2310,
            2270,
            2306,
            2311,
            2308,
            2268,
        ],
        "P1": [
            3645,
            2397,
            2398,
            2396,
            2395,
            9828,
            2400,
            2390,
            2393,
            3683,
            2399,
            22401,
            3779,
            2392,
            2389,
        ],
        "P2": [
            9832,
            2329,
            3828,
            9836,
            44,
            3693,
            15317,
            3725,
            3689,
            2327,
            9842,
            2463,
            2317,
            2321,
            3695,
            9830,
            3697,
            9838,
            2312,
            3691,
            2319,
            9840,
            3775,
            2328,
        ],
        "P3": [
            2358,
            2345,
            2344,
            2367,
            17392,
            2348,
            9834,
            2366,
            2361,
            17898,
            2360,
            2354,
            2352,
            9846,
            9848,
            2351,
            2349,
            2346,
            12836,
            17136,
            28974,
        ],
        "P4": [2867, 2868, 2869, 2870, 2871, 2872, 2875, 2876],
    }

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

    alarted = models.BooleanField(default=False)

    # objects = AuditCharacterManager()

    def __str__(self):
        return f"Planet Details Data: {self.character.character.character_name} - {self.planet.planet.name}"

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
        return self.get_planet_expiry_date() < timezone.now()

    def get_production_type(self, type_id):
        for production_type, ids in self._PRODUCTION_IDS.items():
            if type_id in ids:
                return production_type
        return "Unknown"

    def is_production_type(self, type_id, production_type):
        return type_id in self._PRODUCTION_IDS.get(production_type, [])

    def is_p0(self, type_id):
        return self.is_production_type(type_id, "P0")

    def is_p1(self, type_id):
        return self.is_production_type(type_id, "P1")

    def is_p2(self, type_id):
        return self.is_production_type(type_id, "P2")

    def is_p3(self, type_id):
        return self.is_production_type(type_id, "P3")

    def is_p4(self, type_id):
        return self.is_production_type(type_id, "P4")

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
                product_category = self.get_production_type(type_id)
                product_types[type_id] = {
                    "id": type_id,
                    "name": type_data.name,
                    "category": product_category,
                }
        return product_types
