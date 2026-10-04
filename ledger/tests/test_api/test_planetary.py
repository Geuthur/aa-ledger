# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CharacterOwnerFactory,
    CharacterPlanetDetailsFactory,
    CharacterPlanetFactory,
)
from ledger.tests.testdata.integrations.planetary import _planetary_data


class TestPlanetaryApi(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = CharacterOwnerFactory(user=cls.user)
        cls.planet = CharacterPlanetFactory(
            character=cls.owner, upgrade_level=5, num_pins=5
        )
        cls.details = CharacterPlanetDetailsFactory(
            character=cls.owner, planet=cls.planet, **_planetary_data
        )
        cls.base_url = (
            f"{reverse('ledger:index')}api/character/{cls.owner.eve_id}/planets"
        )

    def test_list_should_return_planets_of_character(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.base_url}/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.planet.id)
        self.assertEqual(data[0]["owner"]["character_id"], self.owner.eve_id)
        self.assertTrue(data[0]["expired"])
        self.assertIn("/icon", data[0]["planet"]["type"]["icon"])
        self.assertFalse(data[0]["alarm"])

    def test_list_should_not_return_html(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.base_url}/")

        # Expected Result
        self.assertNotIn("<", response.content.decode())

    def test_list_should_filter_by_planet_id(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.base_url}/?planet_id=0&single=true")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json(), [])

    def test_list_should_return_403_for_foreign_user(self):
        # Test Data
        self.client.force_login(self.user2)

        # Test Action
        response = self.client.get(f"{self.base_url}/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_detail_should_return_planet(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.base_url}/{self.planet.id}/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(data["owner"]["character_id"], self.owner.eve_id)
        self.assertIsInstance(data["factories"], list)
        self.assertIsInstance(data["storage"], list)
        self.assertIsInstance(data["extractors"], list)

    def test_detail_should_return_404_for_unknown_planet(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.base_url}/0/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_toggle_notification_should_switch_all_planets(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(f"{self.base_url}/notification/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.json()["notification"])
        self.details.refresh_from_db()
        self.assertTrue(self.details.notification)

    def test_toggle_notification_should_return_404_for_unknown_planet(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(f"{self.base_url}/notification/?planet_id=0")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
