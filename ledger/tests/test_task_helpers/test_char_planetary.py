from unittest.mock import MagicMock, patch

from django.test import TestCase
from esi.models import Token
from eveuniverse.models import EvePlanet

from ledger.task_helpers.plan_helpers import update_character_planetary
from ledger.tests.testdata.esi_stub import esi_client_stub
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all
from ledger.tests.testdata.load_planetary import load_planetary

MODULE_PATH = "ledger.task_helpers.plan_helpers"


class TestCharacterPlanetaryHelpers(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()
        load_planetary()

        cls.mock_token = MagicMock(spec=Token)
        cls.mock_token.character_id = 1001
        cls.mock_token.valid_access_token.return_value = "token"

        cls.planetary = [
            {
                "planet_id": 4001,
                "upgrade_level": 5,
                "num_pins": 10,
            },
            {
                "planet_id": 4002,
                "upgrade_level": 4,
                "num_pins": 8,
            },
        ]

        cls.planetarydetails = ""

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".CharacterPlanet.objects")
    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".EvePlanet.objects.get_or_create_esi")
    def test_update_character_planetary(
        self,
        mock_get_or_create_esi,
        mock_etag,
        mock_esi,
        mock_planet_details,
        mock_planet,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client = esi_client_stub
        # TODO get Data from Test ESI
        # mock_etag.return_value = mock_esi.client.Wallet.get_characters_character_id_wallet_journal(character_id=1001)
        mock_etag.return_value = self.planetary

        # Mock the EvePlanet get_or_create_esi method
        mock_get_or_create_esi.side_effect = [
            (EvePlanet.objects.get(id=4001), False),  # Existing planet
            (
                EvePlanet(
                    id=4003,
                    name="Test Planet III",
                    last_updated="2021-01-01T00:00:00Z",
                    position_x=0.0,
                    position_y=0.0,
                    position_z=0.0,
                    eve_solar_system_id=30004783,
                    eve_type_id=13,
                    enabled_sections=0,
                ),
                True,
            ),  # New planet
        ]
        # Mock the current planets
        mock_planet.filter.return_value.values_list.return_value = [4001]

        # when
        result = update_character_planetary(1001)

        # then
        self.assertEqual(result, ("Finished planets update for: %s", "Gneuten"))

        # Verify that the new planets were created
        self.assertEqual(mock_planet.bulk_update.call_count, 1)

        # Verify that obsolete planets were deleted
        self.assertEqual(mock_planet.filter.return_value.delete.call_count, 1)
        self.assertEqual(mock_planet_details.filter.return_value.delete.call_count, 1)

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".CharacterPlanet.objects")
    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".EvePlanet.objects.get_or_create_esi")
    def test_update_character_planetary_exist(
        self,
        mock_get_or_create_esi,
        mock_etag,
        mock_esi,
        mock_planet_details,
        mock_planet,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client = esi_client_stub
        # TODO get Data from Test ESI
        # mock_etag.return_value = mock_esi.client.Wallet.get_characters_character_id_wallet_journal(character_id=1001)
        mock_etag.return_value = self.planetary

        # Mock the EvePlanet get_or_create_esi method
        mock_get_or_create_esi.return_value = (EvePlanet.objects.get(id=4001), False)
        # Mock the current planets
        mock_planet.filter.return_value.values_list.return_value = [4001]

        # when
        result = update_character_planetary(1001)

        # then
        self.assertEqual(result, ("Finished planets update for: %s", "Gneuten"))

        # Verify that the new planets were created
        self.assertEqual(mock_planet.bulk_update.call_count, 1)

        # Verify that obsolete planets were deleted
        self.assertEqual(mock_planet.filter.return_value.delete.call_count, 1)
        self.assertEqual(mock_planet_details.filter.return_value.delete.call_count, 1)

    @patch(MODULE_PATH + ".get_token")
    def test_update_character_planetary_no_token(self, mock_get_token):
        # given
        mock_get_token.return_value = None
        # when
        result = update_character_planetary(1001)
        # then
        self.assertEqual(result, ("No Tokens"))
