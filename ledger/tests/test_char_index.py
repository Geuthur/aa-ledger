from unittest.mock import Mock, patch

from memberaudit.models import Character

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from esi.models import Token

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import create_user_from_evecharacter

from ledger.models.characteraudit import CharacterAudit
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_memberaudit import load_memberaudit
from ledger.views.character.char_audit import add_char, fetch_memberaudit

MODULE_PATH = "ledger.views.character.char_audit"


class CharAuditTest(TestCase):
    def setUp(self):
        self.character = EveCharacter.objects.create(
            character_id=1004,
            character_name="Test Character",
            corporation_id=1004,
            corporation_name="Test Corp",
            alliance_id=1004,
            alliance_name="Test Alliance",
        )
        self.char_audit = CharacterAudit.objects.create(character=self.character)

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        load_memberaudit()
        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
                "ledger.admin_access",
                "ledger.char_audit_admin_access",
            ],
        )

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".update_character")
    def test_add_char(self, mock_update_character, _):
        self.client.force_login(self.user)
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
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("ledger:ledger_index"))
        self.assertTrue(mock_update_character.apply_async.called)
        print(mock_update_character.apply_async.call_args_list)
        self.assertTrue(
            CharacterAudit.objects.get(character=self.character_ownership.character)
        )

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".update_character")
    def test_fetch_memberaudit_updates(self, mock_update_character, mock_messages):
        self.client.force_login(self.user)
        request = self.factory.get(reverse("ledger:ledger_fetch_memberaudit"))
        request.user = self.user
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = fetch_memberaudit(request)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("ledger:ledger_index"))
        self.assertTrue(mock_messages.info.called)
        mock_messages.info.assert_called_with(
            request, "3 Char(s) successfully added/updated to Ledger"
        )
        self.assertTrue(mock_update_character.apply_async.called)
        self.assertTrue(
            CharacterAudit.objects.get(character=self.character_ownership.character)
        )

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".update_character")
    @patch(MODULE_PATH + ".CharacterAudit.objects.get_or_create")
    def test_fetch_memberaudit_no_updates(
        self, mock_char_audit, mock_update_character, mock_messages
    ):
        # Set last_update_wallet to now to prevent update
        char_audit = Mock()
        char_audit.last_update_wallet = timezone.now()
        mock_char_audit.return_value = (char_audit, False)

        self.client.force_login(self.user)
        request = self.factory.get(reverse("ledger:ledger_fetch_memberaudit"))
        request.user = self.user
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = fetch_memberaudit(request)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("ledger:ledger_index"))
        self.assertTrue(mock_messages.info.called)
        mock_messages.info.assert_called_with(request, "No Updates initialized.")
        self.assertFalse(mock_update_character.apply_async.called)

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".update_character")
    @patch("memberaudit.models.Character.objects.filter")
    def test_fetch_memberaudit_general_error(
        self, mock_filter, mock_update_character, mock_messages
    ):
        mock_filter.side_effect = Exception
        self.client.force_login(self.user)
        request = self.factory.get(reverse("ledger:ledger_fetch_memberaudit"))
        request.user = self.user
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = fetch_memberaudit(request)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertTrue(mock_messages.error.called)
        mock_messages.error.assert_called_with(
            request, "An error occurred: Please inform your Admin."
        )
        self.assertFalse(mock_update_character.apply_async.called)
        self.assertEqual(response.url, reverse("ledger:ledger_index"))

    @patch(MODULE_PATH + ".messages")
    @patch(MODULE_PATH + ".update_character")
    @patch("memberaudit.models.Character.objects.filter")
    def test_fetch_memberaudit_import_error(
        self, mock_filter, mock_update_character, mock_messages
    ):
        mock_filter.side_effect = ImportError
        self.client.force_login(self.user)
        request = self.factory.get(reverse("ledger:ledger_fetch_memberaudit"))
        request.user = self.user
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = fetch_memberaudit(request)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertTrue(mock_messages.error.called)
        mock_messages.error.assert_called_with(
            request,
            "The 'memberaudit' app is not installed. Please make sure it is installed.",
        )
        self.assertFalse(mock_update_character.apply_async.called)
        self.assertEqual(response.url, reverse("ledger:ledger_index"))
