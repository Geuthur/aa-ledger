from unittest.mock import MagicMock, call, patch

from django.test import TestCase
from django.utils import timezone
from esi.models import Token
from eveuniverse.models import EvePlanet, EveSolarSystem, EveType

from ledger.models.characteraudit import CharacterAudit
from ledger.models.planetary import CharacterPlanet, CharacterPlanetDetails
from ledger.task_helpers.etag_helpers import NotModifiedError
from ledger.task_helpers.plan_helpers import (
    convert_datetime_to_str,
    update_character_planetary,
    update_character_planetary_details,
)
from ledger.tasks import update_char_planets_details
from ledger.tests.testdata.esi_stub import esi_client_stub
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all
from ledger.tests.testdata.load_planetary import load_planetary
from ledger.tests.testdata.planetary import planetary_data

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

        cls.planetarydetails = planetary_data

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".CharacterPlanet.objects.filter")
    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".EvePlanet.objects.get_or_create_esi")
    @patch(MODULE_PATH + ".CharacterPlanet.objects.bulk_update")
    def test_update_character_planetary(
        self,
        mock_update,
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

        mock_get_or_create_esi.side_effect = [
            (EvePlanet.objects.get(id=4001), False),  # Existing planet
            (
                EvePlanet.objects.create(
                    id=4003,
                    name="Test Planet III",
                    last_updated="2021-01-01T00:00:00Z",
                    position_x=0.0,
                    position_y=0.0,
                    position_z=0.0,
                    eve_solar_system=EveSolarSystem.objects.get(id=30004783),
                    eve_type=EveType.objects.get(id=13),
                    enabled_sections=0,
                ),
                True,
            ),  # New planet
        ]
        mock_planet.return_value.values_list.return_value = [4001]

        # when
        result = update_character_planetary(1001)

        # then
        self.assertEqual(result, ("Finished planets update for: %s", "Gneuten"))
        self.assertEqual(mock_update.call_count, 1)
        self.assertEqual(mock_planet.filter.return_value.delete.call_count, 0)
        self.assertEqual(mock_planet_details.filter.return_value.delete.call_count, 1)

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".CharacterPlanet.objects.filter")
    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".EvePlanet.objects.get_or_create_esi")
    @patch(MODULE_PATH + ".CharacterPlanet.objects.bulk_update")
    def test_update_character_planetary_exist(
        self,
        mock_planet_update,
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
        mock_get_or_create_esi.return_value = (EvePlanet.objects.get(id=4001), False)
        mock_planet.return_value.values_list.return_value = [4001]

        # when
        result = update_character_planetary(1001)

        # then
        self.assertEqual(result, ("Finished planets update for: %s", "Gneuten"))
        self.assertEqual(mock_planet_update.call_count, 1)
        self.assertEqual(mock_planet.filter.return_value.delete.call_count, 0)
        self.assertEqual(mock_planet_details.filter.return_value.delete.call_count, 1)

    @patch(MODULE_PATH + ".get_token")
    def test_update_character_planetary_no_token(self, mock_get_token):
        # given
        mock_get_token.return_value = None
        # when
        result = update_character_planetary(1001)
        # then
        self.assertEqual(result, ("No Tokens"))

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".CharacterPlanet.objects.filter")
    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".EvePlanet.objects.get_or_create_esi")
    @patch(MODULE_PATH + ".CharacterPlanet.objects.bulk_update")
    def test_update_character_planetary_existing_planets(
        self,
        mock_planet_update,
        mock_get_or_create_esi,
        mock_etag,
        mock_esi,
        mock_planet_details,
        mock_planet,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client = MagicMock()
        mock_etag.return_value = [
            {"planet_id": 4001, "upgrade_level": 1, "num_pins": 5},
            {"planet_id": 4002, "upgrade_level": 2, "num_pins": 10},
        ]
        mock_planet.return_value.values_list.return_value = [4001, 4002]

        mock_get_or_create_esi.side_effect = [
            (EvePlanet(id=4001, name="Planet 1"), False),
            (EvePlanet(id=4002, name="Planet 2"), False),
        ]

        # when
        result = update_character_planetary(1001)

        # then
        self.assertEqual(result, ("Finished planets update for: %s", "Gneuten"))
        self.assertEqual(mock_planet_update.call_count, 1)

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".CharacterPlanet.objects.filter")
    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".EvePlanet.objects.get_or_create_esi")
    @patch(MODULE_PATH + ".CharacterPlanet.objects.get")
    @patch(MODULE_PATH + ".CharacterPlanet.objects.bulk_create")
    def test_update_character_planetary_planet_not_exist(
        self,
        mock_planet_create,
        mock_get_planet,
        mock_get_or_create_esi,
        mock_etag,
        mock_esi,
        mock_planet_details,
        mock_planet,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client = MagicMock()
        mock_etag.return_value = [
            {"planet_id": 4004, "upgrade_level": 1, "num_pins": 5},
        ]
        mock_planet.return_value.values_list.return_value = []

        mock_get_or_create_esi.side_effect = [
            (
                EvePlanet.objects.create(
                    id=4004,
                    name="Planet 1",
                    last_updated="2021-01-01T00:00:00Z",
                    position_x=0.0,
                    position_y=0.0,
                    position_z=0.0,
                    eve_solar_system=EveSolarSystem.objects.get(id=30004783),
                    eve_type=EveType.objects.get(id=13),
                    enabled_sections=0,
                ),
                True,
            ),
        ]

        mock_get_planet.side_effect = CharacterPlanet.DoesNotExist

        # when
        result = update_character_planetary(1001)

        # then
        self.assertEqual(result, ("Finished planets update for: %s", "Gneuten"))
        self.assertEqual(mock_planet_create.call_count, 1)

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".logger")
    def test_update_character_planetary_not_modified(
        self,
        mock_logger,
        mock_etag,
        mock_esi,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client = MagicMock()
        mock_etag.side_effect = NotModifiedError

        # when
        result = update_character_planetary(1002)

        # then
        self.assertEqual(result, ("Finished planets update for: %s", "rotze Rotineque"))
        mock_logger.debug.assert_called_with(
            "No New Planet data for: %s", "rotze Rotineque"
        )


class TestCharacterPlanetaryDetailsHelpers(TestCase):
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

        cls.planetarydetails = planetary_data

    @patch(MODULE_PATH + ".get_token")
    def test_update_character_planetarydetails_no_token(self, mock_get_token):
        # given
        mock_get_token.return_value = None
        # when
        result = update_character_planetary_details(1001, 4001)
        # then
        self.assertEqual(result, ("No Tokens"))

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.update_or_create")
    def test_update_character_planetarydetails_exist(
        self,
        mock_update_or_create,
        mock_etag,
        mock_esi,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client.return_value = "Test ESI"
        # TODO get Data from Test ESI
        mock_etag.return_value = self.planetarydetails

        mock_update_or_create.return_value = (
            CharacterPlanetDetails(
                planet=CharacterPlanet.objects.get(
                    character__character__character_id=1001,
                    planet_id=4001,
                ),
                links=self.planetarydetails["links"],
                pins=self.planetarydetails["pins"],
                routes=self.planetarydetails["routes"],
                last_update=timezone.now(),
            ),
            False,
        )

        # when
        result = update_character_planetary_details(1001, 4001)

        # then
        self.assertEqual(result, ("Finished planets details update for: %s", "Gneuten"))

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.update_or_create")
    def test_update_character_planetarydetails_new_details(
        self,
        mock_update_or_create,
        mock_etag,
        mock_esi,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client.return_value = "Test ESI"
        # TODO get Data from Test ESI
        mock_etag.return_value = self.planetarydetails

        planet = EvePlanet.objects.create(
            id=4099,
            name="Planet 1",
            last_updated="2021-01-01T00:00:00Z",
            position_x=0.0,
            position_y=0.0,
            position_z=0.0,
            eve_solar_system=EveSolarSystem.objects.get(id=30004783),
            eve_type=EveType.objects.get(id=13),
            enabled_sections=0,
        )

        CharacterPlanet.objects.create(
            character=CharacterAudit.objects.get(character__character_id=1001),
            planet=planet,
            upgrade_level=5,
            num_pins=5,
        )

        mock_update_or_create.return_value = (
            CharacterPlanetDetails(
                planet=CharacterPlanet.objects.get(
                    character__character__character_id=1001,
                    planet_id=4099,
                ),
                links=self.planetarydetails["links"],
                pins=self.planetarydetails["pins"],
                routes=self.planetarydetails["routes"],
                last_update=timezone.now(),
            ),
            True,
        )

        # when
        result = update_character_planetary_details(1001, 4099)

        # then
        self.assertEqual(result, ("Finished planets details update for: %s", "Gneuten"))

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.update_or_create")
    @patch(MODULE_PATH + ".logger")
    def test_update_character_planetarydetails_expired_no_alert(
        self,
        mock_logger,
        mock_update_or_create,
        mock_etag,
        mock_esi,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client.Planetary_Interaction.get_characters_character_id_planets_planet_id.return_value = (
            self.planetarydetails
        )
        mock_etag.return_value = self.planetarydetails

        mock_update_or_create.return_value = (
            CharacterPlanetDetails(
                planet=CharacterPlanet.objects.get(
                    character__character__character_id=1001,
                    planet_id=4001,
                ),
                links=self.planetarydetails["links"],
                pins=self.planetarydetails["pins"],
                routes=self.planetarydetails["routes"],
                last_update=timezone.now(),
                last_alert=None,
            ),
            False,
        )

        # when
        result = update_character_planetary_details(1001, 4001)

        # then
        self.assertEqual(result, ("Finished planets details update for: %s", "Gneuten"))
        mock_logger.debug.assert_called_with(
            "Planet %s Extractor Heads Expired for: %s", "Test Planet I", "Gneuten"
        )

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.update_or_create")
    @patch(MODULE_PATH + ".logger")
    def test_update_character_planetarydetails_alert_reset(
        self,
        mock_logger,
        mock_update_or_create,
        mock_etag,
        mock_esi,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client.Planetary_Interaction.get_characters_character_id_planets_planet_id.return_value = (
            self.planetarydetails
        )
        mock_etag.return_value = self.planetarydetails

        mock_update_or_create.return_value = (
            CharacterPlanetDetails(
                planet=CharacterPlanet.objects.get(
                    character__character__character_id=1001,
                    planet_id=4002,
                ),
                links=self.planetarydetails["links"],
                pins=self.planetarydetails["pins"],
                routes=self.planetarydetails["routes"],
                last_update=timezone.now(),
                last_alert=timezone.now() - timezone.timedelta(days=2),
            ),
            False,
        )

        # when
        result = update_character_planetary_details(1001, 4002)

        # then
        self.assertEqual(result, ("Finished planets details update for: %s", "Gneuten"))
        mock_logger.debug.assert_called_with(
            "Notification Reseted for %s Planet: %s", "Gneuten", "Test Planet I"
        )

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".logger")
    def test_update_character_planetarydetails_not_modified(
        self,
        mock_logger,
        mock_etag,
        mock_esi,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client = MagicMock()
        mock_etag.side_effect = NotModifiedError

        # when
        result = update_character_planetary_details(1001, 4001)

        # then
        self.assertEqual(result, ("No New Planet Details data for: %s", "Gneuten"))
        mock_logger.debug.assert_called_with(
            "No New Planet Details data for: %s", "Gneuten"
        )

    def test_convert_datetime_to_str(self):
        # given
        sample_datetime = timezone.now()
        sample_data = {"name": "test", "timestamp": sample_datetime}

        # when
        result = convert_datetime_to_str(sample_data)

        # then
        self.assertEqual(result["timestamp"], sample_datetime.isoformat())
