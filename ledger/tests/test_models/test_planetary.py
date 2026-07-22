# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import CharacterOwnerFactory
from ledger.tests.testdata.integrations.planetary import _planetary_data
from ledger.tests.testdata.utils import (
    create_character_planet,
    create_character_planet_details,
)

MODULE_PATH = "ledger.models.planetary"


class TestPlanetModel(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.planet_params = {
            "upgrade_level": 5,
            "num_pins": 5,
        }

        cls.owner = CharacterOwnerFactory(user=cls.user)
        cls.planetary = create_character_planet(
            owner=cls.owner, planet_id=4001, **cls.planet_params
        )

    def test_str(self):
        self.assertEqual(
            str(self.planetary),
            f"Planet Data: {self.planetary.character.character_name} - Test Planet I",
        )

    def test_get_esi_scopes(self):
        self.assertEqual(
            self.planetary.get_esi_scopes(), ["esi-planets.manage_planets.v1"]
        )


class TestPlanetaryDetailsModel(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.planet_params = {
            "upgrade_level": 5,
            "num_pins": 5,
        }

        cls.owner = CharacterOwnerFactory(user=cls.user)
        cls.planetary = create_character_planet(
            owner=cls.owner, planet_id=4001, **cls.planet_params
        )
        cls.planetarydetails = create_character_planet_details(
            cls.planetary, **_planetary_data
        )

    def test_details_str(self):
        self.assertEqual(
            str(self.planetarydetails),
            f"Planet Details Data: {self.planetarydetails.planet.character.character_name} - Test Planet I",
        )

    def test_is_expired(self):
        self.assertEqual(self.planetarydetails.is_expired, True)
