"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo
from allianceauth.eveonline.providers import Alliance, ObjectNotFound

# AA Ledger
from ledger.tests.testdata.generate_corporationaudit import (
    create_user_from_evecharacter,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse
from ledger.views.alliance.add_ally import add_ally

MODULE_PATH = "ledger.views.alliance.add_ally"


@patch(MODULE_PATH + ".messages")
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestAddAllyView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
                "ledger.advanced_access",
            ],
        )
        cls.alliance = Alliance(
            id=3005,
            name="Test Alliance",
            ticker="T.E.S.T",
            corp_ids=[2001, 2002],
            executor_corp_id=None,
            faction_id=None,
        )

    def _add_alliance(self, user, token):
        request = self.factory.get(reverse("ledger:add_ally"))
        request.user = user
        request.token = token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        orig_view = add_ally.__wrapped__.__wrapped__.__wrapped__
        return orig_view(request, token)

    def test_add_ally_already_exist(self, mock_messages):
        # given
        user = self.user
        token = user.token_set.get(character_id=1001)
        # when
        response = self._add_alliance(user, token)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("ledger:alliance_ledger", args=[3001]))
        self.assertEqual(mock_messages.info.call_count, 1)

    @patch(MODULE_PATH + ".provider")
    @patch(MODULE_PATH + ".EveAllianceInfo.objects.get_or_create")
    @patch(MODULE_PATH + ".EveAllianceInfo.objects.get")
    def test_add_ally_does_not_exist(
        self, mock_get, mock_get_or_create, mock_provider, mock_messages
    ):
        # given
        mock_get.side_effect = EveAllianceInfo.DoesNotExist
        mock_provider.get_alliance.return_value = self.alliance

        mock_ally = Mock()
        mock_ally.populate_alliance = Mock()
        mock_ally.alliance_id = 3005
        mock_ally.alliance_name = "Test Alliance"
        mock_ally.alliance_ticker = "T.E.S.T"
        mock_ally.executor_corp_id = 2001
        mock_get_or_create.return_value = (mock_ally, True)
        user = self.user
        token = user.token_set.get(character_id=1001)
        # when
        response = self._add_alliance(user, token)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("ledger:alliance_ledger", args=[3005]))
        self.assertEqual(mock_messages.success.call_count, 1)
        mock_get.assert_called_once_with(alliance_id=3001)
        mock_provider.get_alliance.assert_called_once_with(3001)
        mock_get_or_create.assert_called_once()

    @patch(MODULE_PATH + ".provider")
    @patch(MODULE_PATH + ".EveAllianceInfo.objects.get_or_create")
    @patch(MODULE_PATH + ".EveAllianceInfo.objects.get")
    def test_add_ally_does_not_exist_object_not_found(
        self, mock_get, mock_get_or_create, mock_provider, mock_messages
    ):
        # given
        mock_get.side_effect = EveAllianceInfo.DoesNotExist
        mock_provider.get_alliance.side_effect = ObjectNotFound(3001, "alliance")

        user = self.user
        token = user.token_set.get(character_id=1001)
        # when
        response = self._add_alliance(user, token)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("ledger:alliance_ledger", args=[3001]))
        self.assertEqual(mock_messages.warning.call_count, 1)
        mock_get_or_create.assert_not_called()
