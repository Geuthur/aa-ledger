from http import HTTPStatus
from unittest.mock import MagicMock, Mock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ObjectDoesNotExist
from django.test import RequestFactory, TestCase
from django.urls import reverse

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import create_user_from_evecharacter

from ledger.models.planetary import CharacterPlanetDetails
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.views.character.planetary import planetary_ledger, switch_alarm

MODULE_PATH = "ledger.views.character.planetary"


class CharPlaneterayTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
            ],
        )
        cls.user2, cls.character_ownership = create_user_from_evecharacter(
            1002,
            permissions=[
                "ledger.basic_access",
            ],
        )

    def test_planetary_ledger_view(self):
        request = self.factory.get(
            reverse("ledger:planetary_ledger", kwargs={"character_pk": 0})
        )
        request.user = self.user
        response = planetary_ledger(request, 0)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".get_character")
    @patch(MODULE_PATH + ".CharacterPlanetDetails")
    def test_switch_alarm_valid(
        self, mock_character_planet_details, mock_get_character, mock_messages
    ):
        request = self.factory.post(
            reverse("ledger:planetary_ledger", kwargs={"character_pk": 1001})
        )
        request.user = self.user
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        mock_get_character.return_value = (True, MagicMock(character_id=1001))
        mock_character_planet_details.objects.filter.return_value = [
            MagicMock(notification=False)
        ]

        response = switch_alarm(request, [1001], 1)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("ledger:planetary_ledger", kwargs={"character_pk": 0})
        )

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".get_character")
    @patch(MODULE_PATH + ".CharacterPlanetDetails")
    def test_switch_alarm_all_planets(
        self, mock_character_planet_details, mock_get_character, mock_messages
    ):
        request = self.factory.post(
            reverse("ledger:planetary_ledger", kwargs={"character_pk": 1001})
        )
        request.user = self.user
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        mock_get_character.return_value = (True, MagicMock(character_id=1001))
        mock_character_planet_details.objects.filter.return_value = [
            MagicMock(notification=False)
        ]

        response = switch_alarm(request, [1001], 0)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("ledger:planetary_ledger", kwargs={"character_pk": 0})
        )

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".get_character")
    @patch(MODULE_PATH + ".CharacterPlanetDetails")
    def test_switch_alarm_all_planets_and_alts(
        self, mock_character_planet_details, mock_get_character, mock_messages
    ):
        request = self.factory.post(
            reverse("ledger:planetary_ledger", kwargs={"character_pk": 1001})
        )
        request.user = self.user
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        mock_get_character.return_value = (True, MagicMock(character_id=1001))
        mock_character_planet_details.objects.filter.return_value = [
            MagicMock(notification=False)
        ]

        response = switch_alarm(request, 0, 0)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("ledger:planetary_ledger", kwargs={"character_pk": 0})
        )

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".get_character")
    @patch(MODULE_PATH + ".CharacterPlanetDetails")
    def test_switch_alarm_invalid_character(
        self, mock_character_planet_details, mock_get_character, mock_messages
    ):
        request = self.factory.post(
            reverse("ledger:planetary_ledger", kwargs={"character_pk": 0})
        )
        request.user = self.user
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        mock_get_character.return_value = (False, None)

        response = switch_alarm(request, [9999], 1)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("ledger:planetary_ledger", kwargs={"character_pk": 0})
        )

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".get_character")
    @patch(MODULE_PATH + ".CharacterPlanetDetails")
    def test_switch_alarm_invalid_planet(
        self, mock_character_planet_details, mock_get_character, mock_messages
    ):
        request = self.factory.post(
            reverse("ledger:planetary_ledger", kwargs={"character_pk": 1001})
        )
        request.user = self.user
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        mock_get_character.return_value = (True, MagicMock(character_id=1001))
        mock_character_planet_details.side_effect = CharacterPlanetDetails.DoesNotExist

        response = switch_alarm(request, [1001], 9999)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("ledger:planetary_ledger", kwargs={"character_pk": 0})
        )

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".get_character")
    def test_switch_alarm_no_planets(self, mock_get_character, mock_messages):
        request = self.factory.post(
            reverse("ledger:planetary_ledger", kwargs={"character_pk": 1001})
        )
        request.user = self.user
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        mock_get_character.return_value = (True, MagicMock(character_id=1001))

        response = switch_alarm(request, [1001], 9999)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("ledger:planetary_ledger", kwargs={"character_pk": 0})
        )

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".get_character")
    @patch(MODULE_PATH + ".CharacterPlanetDetails.objects.filter")
    def test_switch_alarm_no_permission(
        self, mock_character_planet_details, mock_get_character, mock_messages
    ):
        request = self.factory.post(
            reverse("ledger:planetary_ledger", kwargs={"character_pk": 1001})
        )
        request.user = self.user2
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)

        mock_get_character.return_value = (False, None)

        response = switch_alarm(request, [1001], 1)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("ledger:planetary_ledger", kwargs={"character_pk": 0})
        )
