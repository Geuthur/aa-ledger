"""TestView class."""

import json
from http import HTTPStatus
from unittest.mock import Mock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ObjectDoesNotExist
from django.test import RequestFactory, TestCase
from django.urls import reverse

from ledger.models.planetary import CharacterPlanetDetails
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
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse
from ledger.views.character import planetary

PLANETARY_PATH = "ledger.views.character.planetary"


@patch(PLANETARY_PATH + ".messages")
class TestViewSwitchAlarm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.planet_params = {
            "upgrade_level": 5,
            "num_pins": 5,
            "last_update": None,
        }

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )
        cls.user_nopermission, cls.character_ownership_no_pm = (
            create_user_from_evecharacter_with_access(1002)
        )
        cls.audit = add_charactermaudit_character_to_user(cls.user, 1001)
        cls.planetary = create_character_planet(cls.audit, 4001, **cls.planet_params)
        cls.planetarydetails = create_character_planet_details(
            cls.planetary, **_planetary_data
        )

    def test_switch_alarm(self, mock_messages):
        character_id = self.audit.character.character_id
        form_data = {
            "character_id": character_id,
            "planet_id": 4001,
            "confirm": "yes",
        }

        request = self.factory.post(
            reverse("ledger:switch_alarm", args=[character_id, 4001]),
            data=form_data,
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        request.user = self.user

        response = planetary.switch_alarm(
            request, character_id=character_id, planet_id=4001
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(mock_messages.info.called)

    def test_switch_alarm_all(self, mock_messages):
        form_data = {
            "character_id": 0,
            "planet_id": 0,
            "confirm": "yes",
        }

        request = self.factory.post(
            reverse("ledger:switch_alarm", args=[0, 0]),
            data=form_data,
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        request.user = self.user

        response = planetary.switch_alarm(request, character_id=0, planet_id=0)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(mock_messages.info.called)

    @patch(PLANETARY_PATH + ".CharacterPlanetDetails.objects.filter")
    def test_switch_alarm_doesnotexist(self, mock_planetdetails_filter, mock_messages):
        form_data = {
            "character_id": 1001,
            "planet_id": 0,
            "confirm": "yes",
        }

        mock_planetdetails_filter.return_value = []

        request = self.factory.post(
            reverse("ledger:switch_alarm", args=[1001, 0]),
            data=form_data,
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        request.user = self.user

        response = planetary.switch_alarm(request, character_id=0, planet_id=0)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(mock_messages.error.called)
        mock_planetdetails_filter.assert_called_once()

    def test_switch_alarm_no_permission(self, mock_messages):
        form_data = {
            "character_id": 1001,
            "planet_id": 4001,
            "confirm": "yes",
        }
        request = self.factory.post(
            reverse("ledger:switch_alarm", args=[1001, 4001]),
            data=form_data,
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        request.user = self.user_nopermission

        response = planetary.switch_alarm(request, character_id=1001, planet_id=4001)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(mock_messages.error.called)

    def test_switch_alarm_invalid(self, mock_messages):
        request = self.factory.post(
            reverse("ledger:switch_alarm", args=[1001, 4001]),
            data=None,
        )
        request.user = self.user

        response = planetary.switch_alarm(request, character_id=1001, planet_id=4001)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(mock_messages.error.called)
