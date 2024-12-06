"""
Planetary Model
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from eveuniverse.models import EvePlanet, EveType

from ledger.hooks import get_extension_logger
from ledger.managers.planetary_manager import PlanetaryManager
from ledger.models.characteraudit import CharacterAudit

logger = get_extension_logger(__name__)

SPACEPORTS = [2256, 2542, 2543, 2544, 2552, 2555, 2556, 2557]
STORAGE_FACILITY = [2257, 2535, 2536, 2541, 2558, 2560, 2561, 2562]
EXTRACTOR_CONTROL_UNIT = [2848, 3060, 3061, 3062, 3063, 3064, 3067, 3068]
P0_PRODUCTS_SOLID = [2267, 2270, 2272, 2306, 2307]
P0_PRODUCTS_LIQUID_GAS = [2268, 2308, 2309, 2310, 2311]
P0_PRODUCTS_ORGANIC = [2073, 2286, 2287, 2288, 2305]
P1_PRODUCTS = [
    2389,
    2390,
    2392,
    2393,
    2395,
    2396,
    2397,
    2398,
    2399,
    2400,
    2401,
    3645,
    3683,
    3779,
    9828,
]
P2_PRODUCTS = [
    44,
    2312,
    2317,
    2319,
    2321,
    2327,
    2328,
    2329,
    2463,
    3689,
    3691,
    3693,
    3695,
    3697,
    3725,
    3775,
    3828,
    983,
    9832,
    9836,
    9838,
    9840,
    9842,
    15317,
]
P3_PRODUCTS = [
    2344,
    2345,
    2346,
    2348,
    2349,
    2351,
    2352,
    2354,
    2358,
    2360,
    2361,
    2366,
    2367,
    9834,
    9846,
    9848,
    12836,
    17136,
    17392,
    17898,
    28974,
]
P4_PRODUCTS = [2867, 2868, 2869, 2870, 2871, 2872, 2875, 2876]
P5_PRODUCTS = []


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
