"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse

# AA Ledger
from ledger.tests.testdata.generate_characteraudit import (
    add_characteraudit_character_to_user,
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


class TestViewSwitchAlarm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.planet_params = {
            "upgrade_level": 5,
            "num_pins": 5,
        }

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )
        cls.user_nopermission, cls.character_ownership_no_pm = (
            create_user_from_evecharacter_with_access(1002)
        )
        cls.audit = add_characteraudit_character_to_user(cls.user, 1001)
        cls.planetary = create_character_planet(cls.audit, 4001, **cls.planet_params)
        cls.planetarydetails = create_character_planet_details(
            cls.planetary, **_planetary_data
        )

    def test_switch_alarm(self):
        character_id = self.audit.eve_character.character_id
        form_data = {
            "character_id": character_id,
            "planet_id": 4001,
            "confirm": "yes",
        }

        request = self.factory.post(
            reverse("ledger:switch_alarm"),
            data=form_data,
        )
        request.user = self.user

        response = planetary.switch_alarm(request)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_switch_alarm_all(self):
        form_data = {
            "character_id": 0,
            "planet_id": 0,
            "confirm": "yes",
        }

        request = self.factory.post(
            reverse("ledger:switch_alarm"),
            data=form_data,
        )
        request.user = self.user

        response = planetary.switch_alarm(request)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    @patch(PLANETARY_PATH + ".CharacterPlanetDetails.objects.filter")
    def test_switch_alarm_doesnotexist(self, mock_planetdetails_filter):
        form_data = {
            "character_id": 1001,
            "planet_id": 0,
            "confirm": "yes",
        }

        mock_queryset = Mock()
        mock_queryset.exists.return_value = False
        mock_planetdetails_filter.return_value = mock_queryset

        request = self.factory.post(
            reverse("ledger:switch_alarm"),
            data=form_data,
        )
        request.user = self.user

        response = planetary.switch_alarm(request)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        mock_planetdetails_filter.assert_called_once()

    def test_switch_alarm_no_permission(self):
        form_data = {
            "character_id": 1001,
            "planet_id": 4001,
            "confirm": "yes",
        }
        request = self.factory.post(
            reverse("ledger:switch_alarm"),
            data=form_data,
        )
        request.user = self.user_nopermission

        response = planetary.switch_alarm(request)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_switch_alarm_invalid(self):
        request = self.factory.post(
            reverse("ledger:switch_alarm"),
            data=None,
        )
        request.user = self.user

        response = planetary.switch_alarm(request)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
