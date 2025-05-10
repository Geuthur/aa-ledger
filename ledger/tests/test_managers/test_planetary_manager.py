# Standard Library
from sys import audit
from unittest.mock import patch

# Django
from django.test import override_settings
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests.testdata.esi_stub import esi_client_stub
from ledger.tests.testdata.generate_characteraudit import (
    create_characteraudit_character,
)
from ledger.tests.testdata.generate_planets import create_character_planet
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.managers.character_planetary_manager"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch(MODULE_PATH + ".etag_results")
class TestPlanetaryManager(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()
        cls.audit = create_characteraudit_character(1001)

    def test_update_planets(self, mock_etag, mock_esi):
        # given
        mock_esi.client = esi_client_stub
        mock_etag.return_value = [
            {
                "last_update": "2016-10-29T14:00:00Z",
                "num_pins": 5,
                "owner_id": 1001,
                "planet_id": 4001,
                "planet_type": "lava",
                "solar_system_id": 30004783,
                "upgrade_level": 5,
            },
            {
                "last_update": "2016-10-29T14:00:00Z",
                "num_pins": 5,
                "owner_id": 1001,
                "planet_id": 4002,
                "planet_type": "lava",
                "solar_system_id": 30004783,
                "upgrade_level": 5,
            },
        ]

        self.audit.update_planets(force_refresh=False)

        self.assertSetEqual(
            set(self.audit.ledger_character_planet.values_list("planet_id", flat=True)),
            {4001, 4002},
        )
        obj = self.audit.ledger_character_planet.get(planet_id=4001)
        self.assertEqual(obj.planet_id, 4001)
        self.assertEqual(obj.upgrade_level, 5)
        self.assertEqual(obj.num_pins, 5)

        obj = self.audit.ledger_character_planet.get(planet_id=4002)
        self.assertEqual(obj.planet_id, 4002)
        self.assertEqual(obj.upgrade_level, 5)
        self.assertEqual(obj.num_pins, 5)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch(MODULE_PATH + ".etag_results")
class TestPlanetaryDetailsManager(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()
        cls.audit = create_characteraudit_character(1001)
        cls.planet = create_character_planet(
            characteraudit=cls.audit, planet_id=4001, upgrade_level=5, num_pins=5
        )

    def test_update_planets_details(self, mock_etag, mock_esi):
        # given
        mock_esi.client = esi_client_stub
        mock_etag.return_value = {
            "links": [
                {
                    "destination_pin_id": 1046238237381,
                    "link_level": 0,
                    "source_pin_id": 1046238237375,
                },
                {
                    "destination_pin_id": 1046238237383,
                    "link_level": 0,
                    "source_pin_id": 1046238237381,
                },
            ],
            "pins": [
                {
                    "contents": [],
                    "latitude": 0.015516729094088078,
                    "longitude": 2.3920838832855225,
                    "pin_id": 1046238231981,
                    "type_id": 2534,
                },
                {
                    "contents": [],
                    "expiry_time": "2024-08-26T17:17:02Z",
                    "extractor_details": {
                        "cycle_time": 14400,
                        "head_radius": 0.05000000074505806,
                        "heads": [
                            {
                                "head_id": 0,
                                "latitude": 1.0986779928207397,
                                "longitude": 1.4244794845581055,
                            },
                            {
                                "head_id": 1,
                                "latitude": 1.1128675937652588,
                                "longitude": 1.3068562746047974,
                            },
                        ],
                        "product_type_id": 2268,
                        "qty_per_cycle": 6541,
                    },
                    "install_time": "2024-08-12T17:17:02Z",
                    "last_cycle_start": "2024-08-12T17:17:02Z",
                    "latitude": 0.9115607738494873,
                    "longitude": 1.1501415967941284,
                    "pin_id": 1046238237375,
                    "type_id": 3060,
                },
            ],
            "routes": [
                {
                    "content_type_id": 9832,
                    "destination_pin_id": 1046238237382,
                    "quantity": 5,
                    "route_id": 1381898852,
                    "source_pin_id": 1046238237396,
                    "waypoints": [],
                },
                {
                    "content_type_id": 2309,
                    "destination_pin_id": 1046238237392,
                    "quantity": 3000,
                    "route_id": 1381898867,
                    "source_pin_id": 1046238237381,
                    "waypoints": [1046238237388],
                },
            ],
        }

        self.audit.update_planets_details(force_refresh=False)

        self.assertSetEqual(
            set(
                self.audit.ledger_character_planet_details.values_list(
                    "planet__planet_id", flat=True
                )
            ),
            {4001},
        )
