from ninja import NinjaAPI

from django.test import TestCase

from app_utils.testing import create_user_from_evecharacter

from ledger.api.character.planetary import LedgerPlanetaryApiEndpoints
from ledger.api.schema import Character
from ledger.models.characteraudit import CharacterWalletJournalEntry
from ledger.tests.test_api import _planetchardata
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all
from ledger.tests.testdata.load_planetary import load_planetary


class ManageApiJournalCharEndpointsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()
        load_planetary()

        cls.user, _ = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
            ],
        )

        cls.user2, _ = create_user_from_evecharacter(
            1002,
            permissions=[
                "ledger.basic_access",
            ],
        )
        cls.api = NinjaAPI()
        cls.manage_api_endpoints = LedgerPlanetaryApiEndpoints(api=cls.api)

    def test_get_character_planetary_api(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/0/planetary/0/"

        response = self.client.get(url)
        expected_data = [
            {
                "character_id": 1001,
                "character_name": "Gneuten",
                "planet": "Test Planet I",
                "planet_id": 4001,
                "upgrade_level": 5,
                "num_pins": 5,
                "last_update": None,
            },
            {
                "character_id": 1001,
                "character_name": "Gneuten",
                "planet": "Test Planet I",
                "planet_id": 4002,
                "upgrade_level": 5,
                "num_pins": 5,
                "last_update": None,
            },
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_planetary_api_single(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/1001/planetary/0/"

        response = self.client.get(url)

        expected_data = [
            {
                "character_id": 1001,
                "character_name": "Gneuten",
                "planet": "Test Planet I",
                "planet_id": 4001,
                "upgrade_level": 5,
                "num_pins": 5,
                "last_update": None,
            },
            {
                "character_id": 1001,
                "character_name": "Gneuten",
                "planet": "Test Planet I",
                "planet_id": 4002,
                "upgrade_level": 5,
                "num_pins": 5,
                "last_update": None,
            },
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_planetary_api_single_planet(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/1001/planetary/4001/"

        response = self.client.get(url)

        expected_data = [
            {
                "character_id": 1001,
                "character_name": "Gneuten",
                "planet": "Test Planet I",
                "planet_id": 4001,
                "upgrade_level": 5,
                "num_pins": 5,
                "last_update": None,
            },
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_planetary_api_no_permission(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/account/1001/planetary/0/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), "Permission Denied")

    def test_get_character_planetary_details_api(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/0/planetary/0/details/"

        response = self.client.get(url)
        expected_data = _planetchardata.planet_many

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_planetary_details_api_single(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/1001/planetary/0/details/"

        response = self.client.get(url)

        expected_data = _planetchardata.planet_many

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_planetary_details_api_single_planet(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/1001/planetary/4001/details/"

        response = self.client.get(url)

        expected_data = _planetchardata.planet_single

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_planetary_details_api_no_permission(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/account/1001/planetary/0/details/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), "Permission Denied")
