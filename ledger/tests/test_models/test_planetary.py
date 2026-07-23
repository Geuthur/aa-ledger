# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CharacterOwnerFactory,
    CharacterPlanetDetailsFactory,
    CharacterPlanetFactory,
)
from ledger.tests.testdata.integrations.planetary import _planetary_data

MODULE_PATH = "ledger.models.planetary"


class TestPlanetModel(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = CharacterOwnerFactory(user=cls.user)
        cls.planetary = CharacterPlanetFactory(
            character=cls.owner, upgrade_level=5, num_pins=5
        )

    def test_str(self):
        self.assertEqual(
            str(self.planetary),
            f"Planet Data: {self.planetary.character.character_name} - {self.planetary.eve_planet.name}",
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
        cls.planetary = CharacterPlanetFactory(
            character=cls.owner, upgrade_level=5, num_pins=5
        )
        cls.planetarydetails = CharacterPlanetDetailsFactory(
            character=cls.owner, planet=cls.planetary, **_planetary_data
        )

    def test_details_str(self):
        self.assertEqual(
            str(self.planetarydetails),
            f"Planet Details Data: {self.planetarydetails.planet.character.character_name} - {self.planetarydetails.planet.eve_planet.name}",
        )

    def test_is_expired(self):
        self.assertEqual(self.planetarydetails.is_expired, True)
