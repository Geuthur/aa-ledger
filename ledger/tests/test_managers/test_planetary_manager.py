# Standard Library
from sys import audit
from unittest.mock import MagicMock, patch

# Django
from django.test import override_settings

# Alliance Auth (External Libs)
from eveuniverse.models import EveType

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.esi_stub_openapi import EsiEndpoint, create_esi_client_stub
from ledger.tests.testdata.utils import create_character_planet, create_owner_from_user

MODULE_PATH = "ledger.managers.character_planetary_manager"

LEDGER_CHARACTER_PLANETARY_ENDPOINTS = [
    EsiEndpoint(
        "Planetary_Interaction", "GetCharactersCharacterIdPlanets", "character_id"
    ),
    EsiEndpoint(
        "Planetary_Interaction",
        "GetCharactersCharacterIdPlanetsPlanetId",
        "character_id",
        "planet_id",
    ),
]


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
class TestPlanetaryManager(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(user=cls.user)
        cls.token = cls.user_character.user.token_set.first()
        cls.audit.get_token = MagicMock(return_value=cls.token)

    def test_update_planets(self, mock_esi):
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
        mock_esi.client = create_esi_client_stub(
            endpoints=LEDGER_CHARACTER_PLANETARY_ENDPOINTS
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


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".EveType.objects.get_or_create_esi")
@patch(MODULE_PATH + ".esi")
class TestPlanetaryDetailsManager(LedgerTestCase):
    """Test Planetary Details Manager for Character Planets."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(user=cls.user)
        cls.planet = create_character_planet(
            owner=cls.audit, planet_id=4001, upgrade_level=5, num_pins=5
        )
        cls.token = cls.user_character.user.token_set.first()
        cls.audit.get_token = MagicMock(return_value=cls.token)

    def test_update_planets_details(self, mock_esi, mock_get_or_create_esi):
        """
        Test updating the character planetary details.

        This test verifies that the planetary details for a character's planet are correctly updated
        from ESI data. It checks that the planet details are created with the expected planet IDs.

        ### Expected Result
        - Planetary details are updated correctly.
        - Planet details have correct planet IDs.
        """
        # Test Data
        mock_esi.client = create_esi_client_stub(
            endpoints=LEDGER_CHARACTER_PLANETARY_ENDPOINTS
        )
        eve_type = EveType.objects.get(id=2268)
        mock_get_or_create_esi.return_value = (eve_type, True)

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
