# Standard Library
from http import HTTPStatus
from unittest.mock import MagicMock, patch

# Third Party
import pook

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import CharacterOwnerFactory
from ledger.tests.testdata.utils import create_character_planet

MODULE_PATH = "ledger.managers.character_planetary_manager"


class TestPlanetaryManager(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CharacterOwnerFactory(user=cls.user)
        cls.token = cls.user.token_set.first()
        cls.audit.get_token = MagicMock(return_value=cls.token)

    @pook.on
    def test_update_planets(self):
        """
        Test updating the character planetary data.

        This test verifies that the planetary data for a character is correctly updated
        from ESI data. It checks that the planets have the expected upgrade levels and
        number of pins.

        ### Expected Result
        - Planetary data is updated correctly.
        - Planets have correct upgrade levels and number of pins.
        """
        # Test Data
        pook.get(
            f"https://esi.evetech.net/characters/{self.audit.eve_character.character_id}/planets",
            reply=HTTPStatus.OK,
            response_json=[
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
            ],
        )

        # Test Action
        self.audit.update_planets(force_refresh=False)

        # Excepted Results
        self.assertSetEqual(
            set(
                self.audit.ledger_character_planet.values_list(
                    "eve_planet_id", flat=True
                )
            ),
            {4001, 4002},
        )
        obj = self.audit.ledger_character_planet.get(eve_planet_id=4001)
        self.assertEqual(obj.eve_planet_id, 4001)
        self.assertEqual(obj.upgrade_level, 5)
        self.assertEqual(obj.num_pins, 5)

        obj = self.audit.ledger_character_planet.get(eve_planet_id=4002)
        self.assertEqual(obj.eve_planet_id, 4002)
        self.assertEqual(obj.upgrade_level, 5)
        self.assertEqual(obj.num_pins, 5)


class TestPlanetaryDetailsManager(LedgerTestCase):
    """Test Planetary Details Manager for Character Planets."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CharacterOwnerFactory(user=cls.user)
        cls.planet = create_character_planet(
            owner=cls.audit, planet_id=4001, upgrade_level=5, num_pins=5
        )
        cls.token = cls.user.token_set.first()
        cls.audit.get_token = MagicMock(return_value=cls.token)

    @pook.on
    def test_update_planets_details(self):
        """
        Test updating the character planetary details.

        This test verifies that the planetary details for a character's planet are correctly updated
        from ESI data. It checks that the planet details are created with the expected planet IDs.

        ### Expected Result
        - Planetary details are updated correctly.
        - Planet details have correct planet IDs.
        """
        # Test Data
        pook.get(
            f"https://esi.evetech.net/characters/{self.audit.eve_character.character_id}/planets/{self.planet.eve_planet_id}",
            reply=HTTPStatus.OK,
            response_json={
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
            },
        )

        # Test Action
        self.audit.update_planets_details(force_refresh=False)

        # Excepted Results
        self.assertSetEqual(
            set(
                self.audit.ledger_character_planet_details.values_list(
                    "planet__eve_planet_id", flat=True
                )
            ),
            {4001},
        )
