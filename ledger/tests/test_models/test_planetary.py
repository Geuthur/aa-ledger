# Standard Library
from unittest.mock import patch

# Django
from django.test import TestCase
from django.utils import timezone

# AA Ledger
from ledger.tests.testdata.generate_characteraudit import (
    create_characteraudit_from_evecharacter,
)
from ledger.tests.testdata.generate_planets import (
    _planetary_data,
    create_character_planet,
    create_character_planet_details,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.models.planetary"


class TestPlanetModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.planet_params = {
            "upgrade_level": 5,
            "num_pins": 5,
        }

        cls.audit = create_characteraudit_from_evecharacter(1001)
        cls.planetary = create_character_planet(cls.audit, 4001, **cls.planet_params)

    def test_str(self):
        self.assertEqual(str(self.planetary), "Planet Data: Gneuten - Test Planet I")

    def test_get_esi_scopes(self):
        self.assertEqual(
            self.planetary.get_esi_scopes(), ["esi-planets.manage_planets.v1"]
        )


class TestPlanetaryDetailsModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.planet_params = {
            "upgrade_level": 5,
            "num_pins": 5,
        }

        cls.audit = create_characteraudit_from_evecharacter(1001)
        cls.planetary = create_character_planet(cls.audit, 4001, **cls.planet_params)
        cls.planetarydetails = create_character_planet_details(
            cls.planetary, **_planetary_data
        )

    def test_details_str(self):
        self.assertEqual(
            str(self.planetarydetails), "Planet Details Data: Gneuten - Test Planet I"
        )

    def test_is_expired(self):
        self.assertEqual(self.planetarydetails.is_expired, True)
