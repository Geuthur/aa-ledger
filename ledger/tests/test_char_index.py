from unittest.mock import Mock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse
from esi.models import Token

from app_utils.testing import create_user_from_evecharacter

from ledger.models.characteraudit import CharacterAudit
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.views.character.char_audit import add_char

MODULE_PATH = "ledger.views.character.char_audit"


class AddCharTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001, permissions=["ledger.basic_access"]
        )

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".update_character")
    def test_add_char(self, mock_update_character, mock_messages):
        token = Mock(spec=Token)
        token.character_id = self.character_ownership.character.character_id
        request = self.factory.get(reverse("ledger:ledger_add_char"))
        request.user = self.user
        request.token = token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # given
        orig_view = add_char.__wrapped__.__wrapped__
        # when
        response = orig_view(request, token)
        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.url, reverse("ledger:ledger_index"))
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(mock_update_character.apply_async.called)
        self.assertTrue(
            CharacterAudit.objects.get(character=self.character_ownership.character)
        )