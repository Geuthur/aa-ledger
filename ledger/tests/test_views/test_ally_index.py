from unittest.mock import Mock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse
from esi.models import Token

from allianceauth.eveonline.providers import ObjectNotFound
from app_utils.testing import create_user_from_evecharacter

from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.views.alliance.ally_audit import add_ally

MODULE_PATH = "ledger.views.alliance.ally_audit"


class CharAuditTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
                "ledger.admin_access",
                "ledger.corp_audit_admin_manager",
            ],
        )

        cls.token = Mock(spec=Token)
        cls.token.character_id = cls.character_ownership.character.character_id
        cls.token.corporation_id = cls.character_ownership.character.corporation_id
        cls.token.corporation_name = cls.character_ownership.character.corporation_name
        cls.token.corporation_ticker = (
            cls.character_ownership.character.corporation_ticker
        )
        cls.token.alliance_id = 3001
        cls.token.alliance_name = "Voices of War"
        cls.token.alliance_ticker = "VOW"

    @patch(MODULE_PATH + ".messages")
    def test_add_ally(self, mock_messages):
        self.client.force_login(self.user)
        request = self.factory.get(reverse("ledger:ledger_add_ally"))
        request.user = self.user
        request.token = self.token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # given
        orig_view = add_ally.__wrapped__.__wrapped__
        # when
        response = orig_view(request, self.token)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("ledger:alliance_ledger", kwargs={"alliance_pk": 0})
        )
        self.assertTrue(mock_messages.info.called)

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".EveAllianceInfo.objects.filter")
    @patch(MODULE_PATH + ".provider.get_alliance")
    @patch(MODULE_PATH + ".EveAllianceInfo.objects.get_or_create")
    def test_add_ally_not_exist_create_ally(
        self, mock_get_or_create, mock_get_alliance, mock_ally, mock_messages
    ):
        self.client.force_login(self.user)

        mock_get_alliance.return_value = Mock()
        mock_get_alliance.return_value.id = 9999
        mock_get_alliance.return_value.name = "Voices of War"
        mock_get_alliance.return_value.ticker = "VOW"
        mock_get_alliance.return_value.executor_corp_id = 2001

        mock_ally.return_value.first.return_value = None

        mock_get_or_create.return_value = (Mock(), True)
        mock_ally.populate_alliance.return_value = None

        request = self.factory.get(reverse("ledger:ledger_add_ally"))
        request.user = self.user
        request.token = self.token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # given
        orig_view = add_ally.__wrapped__.__wrapped__
        # when
        response = orig_view(request, self.token)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("ledger:alliance_ledger", kwargs={"alliance_pk": 0})
        )
        self.assertTrue(mock_messages.success.called)

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".EveAllianceInfo.objects.filter")
    @patch(MODULE_PATH + ".provider.get_alliance")
    def test_add_ally_not_exist_object_not_found(
        self, mock_get_alliance, mock_ally, mock_messages
    ):
        self.client.force_login(self.user)

        mock_get_alliance.side_effect = ObjectNotFound(3001, "Alliance not found")

        mock_ally.return_value.first.return_value = None

        request = self.factory.get(reverse("ledger:ledger_add_ally"))
        request.user = self.user
        request.token = self.token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # given
        orig_view = add_ally.__wrapped__.__wrapped__
        # when
        response = orig_view(request, self.token)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("ledger:alliance_ledger", kwargs={"alliance_pk": 0})
        )
        self.assertTrue(mock_messages.warning.called)
