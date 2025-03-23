from unittest.mock import MagicMock, patch

from ninja import NinjaAPI

from django.test import TestCase
from django.utils import timezone

from app_utils.testing import create_user_from_evecharacter

from ledger.api.ledger.planetary import LedgerPlanetaryApiEndpoints
from ledger.tests.test_api import _planetchardata
from ledger.tests.testdata.generate_characteraudit import (
    add_charactermaudit_character_to_user,
    create_user_from_evecharacter_with_access,
)
from ledger.tests.testdata.generate_planets import (
    _planetary_data,
    create_character_planet,
    create_character_planet_details,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse


class ManageApiJournalCharEndpointsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()

        cls.planet_params = {
            "upgrade_level": 5,
            "num_pins": 5,
            "last_update": None,
        }

        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )
        cls.user2, cls.character_ownership2 = create_user_from_evecharacter_with_access(
            1002
        )

        cls.audit = add_charactermaudit_character_to_user(cls.user, 1001)
        cls.planetary = create_character_planet(cls.audit, 4001, **cls.planet_params)
        cls.planetary2 = create_character_planet(cls.audit, 4002, **cls.planet_params)
        cls.planetarydetails = create_character_planet_details(
            cls.planetary, **_planetary_data
        )
        cls.planetarydetails2 = create_character_planet_details(
            cls.planetary2, **_planetary_data
        )

        cls.api = NinjaAPI()
        cls.manage_api_endpoints = LedgerPlanetaryApiEndpoints(api=cls.api)

    def test_get_character_planetary_api(self):
        self.client.force_login(self.user)
        url = "/ledger/api/character/0/planetary/0/"

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
        url = "/ledger/api/character/1001/planetary/0/"

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
        url = "/ledger/api/character/1001/planetary/4001/"

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
        url = "/ledger/api/character/1001/planetary/0/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), "Permission Denied")

    def test_get_character_planetary_details_api(self):
        self.client.force_login(self.user)
        url = "/ledger/api/character/0/planetary/0/details/"

        response = self.client.get(url)
        expected_data = _planetchardata.planet_many

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_planetary_details_all_planets(self):
        self.client.force_login(self.user)
        url = "/ledger/api/character/1001/planetary/0/details/"

        response = self.client.get(url)

        expected_data = _planetchardata.planet_many

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_planetary_details_single_planet_with_no_expired_mock(self):
        self.client.force_login(self.user)
        url = "/ledger/api/character/1001/planetary/4001/details/"

        # Set the fixed date as a timezone-aware datetime object
        fixed_date = timezone.make_aware(timezone.datetime(2024, 8, 20, 17, 17, 2))

        # Mock the timezone.now() method to return the fixed date
        with patch("django.utils.timezone.now", return_value=fixed_date):
            response = self.client.get(url)
            expected_data = _planetchardata.planet_single

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), expected_data)

    def test_get_character_planetary_details_api_no_permission(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/character/1001/planetary/0/details/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), "Permission Denied")

    @patch("ledger.api.ledger.admin.CharacterAudit.objects.visible_eve_characters")
    def test_get_character_overview_planetary_no_visible(self, mock_visible_to):
        self.client.force_login(self.user2)
        url = "/ledger/api/planetary/overview/"

        mock_visible_to.return_value.values_list.return_value = []

        # when
        response = self.client.get(url)
        # then
        self.assertContains(response, "Permission Denied", status_code=403)

    def test_get_character_planetary_overview(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/planetary/overview/"

        # when
        response = self.client.get(url)
        # then
        excepted_data = [
            {
                "character": {
                    "1002": {
                        "character_id": 1002,
                        "character_name": "rotze Rotineque",
                        "corporation_id": 2002,
                        "corporation_name": "Eulenclub",
                    }
                }
            }
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), excepted_data)

    @patch("ledger.api.ledger.admin.UserProfile.objects.filter")
    def test_get_character_overview_planetary_attribute_error(
        self, mock_user_profile_filter
    ):
        # given
        self.client.force_login(self.user)
        url = "/ledger/api/planetary/overview/"

        # Mock the UserProfile to return a character with missing attributes
        mock_user_profile_filter.return_value = [MagicMock(main_character="LUL")]

        # when
        response = self.client.get(url)

        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"character": {}}])
