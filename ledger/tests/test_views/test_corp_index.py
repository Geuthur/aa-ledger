from unittest.mock import Mock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse
from esi.models import Token

from app_utils.testing import create_user_from_evecharacter

from ledger.models.corporationaudit import CorporationAudit
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.views.corporation.corp_audit import add_corp

MODULE_PATH = "ledger.views.corporation.corp_audit"


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

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".update_corp")
    def test_add_corp(self, mock_update_corp, mock_messages):
        self.client.force_login(self.user)
        token = Mock(spec=Token)
        token.character_id = self.character_ownership.character.character_id
        token.corporation_id = self.character_ownership.character.corporation_id
        token.corporation_name = self.character_ownership.character.corporation_name
        token.corporation_ticker = self.character_ownership.character.corporation_ticker
        request = self.factory.get(reverse("ledger:ledger_add_corp"))
        request.user = self.user
        request.token = token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # given
        orig_view = add_corp.__wrapped__.__wrapped__
        # when
        response = orig_view(request, token)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("ledger:corporation_ledger", kwargs={"corporation_pk": 0}),
        )
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(mock_update_corp.apply_async.called)
        self.assertTrue(
            CorporationAudit.objects.get(
                corporation=self.character_ownership.character.corporation
            )
        )
