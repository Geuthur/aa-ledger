from unittest.mock import Mock, patch

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from ledger.views.character.char_audit import add_char, fetch_memberaudit


class AddCharTest(TestCase):
    def setUp(self):
        # Erstellen Sie eine Anfrage und ein Token Mock-Objekt
        self.factory = RequestFactory()
        self.request = self.factory.get("ledger:add_char")
        self.request.user = AnonymousUser()
        self.token = Mock()

    @patch("ledger.views.CharacterAudit.objects.update_or_create")
    @patch("ledger.views.EveCharacter.objects.get_character_by_id")
    @patch("ledger.views.update_character.apply_async")
    @patch("ledger.views.messages.info")
    def test_add_char(
        self,
        mock_info,
        mock_apply_async,
        mock_get_character_by_id,
        mock_update_or_create,
    ):
        # Setzen Sie die Rückgabewerte der Mock-Objekte
        self.token.character_id = "123"
        mock_get_character_by_id.return_value = "Character"

        # Rufen Sie die Funktion auf
        response = add_char(self.request, self.token)

        # Überprüfen Sie, ob die Mock-Objekte aufgerufen wurden
        mock_get_character_by_id.assert_called_once_with("123")
        mock_update_or_create.assert_called_once_with(character="Character")
        mock_apply_async.assert_called_once_with(
            args=["123"], kwargs={"force_refresh": True}, priority=6
        )
        mock_info.assert_called_once_with(
            self.request, "Char successfully added/updated to Ledger"
        )

        # Überprüfen Sie die Antwort
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ledger/index.html")


class FetchMemberAuditTest(TestCase):
    def setUp(self):
        # Erstellen Sie eine Anfrage und ein Character Mock-Objekt
        self.factory = RequestFactory()
        self.request = self.factory.get("ledger:ledger_fetch_memberaudit")
        self.request.user = AnonymousUser()
        self.character = Mock()

    @patch("ledger.views.CharacterAudit.objects.get_or_create")
    @patch("ledger.views.update_character.apply_async")
    @patch("ledger.views.messages.info")
    @patch("ledger.views.messages.error")
    @patch("memberaudit.models.Character.objects.filter")
    def test_fetch_memberaudit(
        self, mock_filter, mock_error, mock_info, mock_apply_async, mock_get_or_create
    ):
        # Setzen Sie die Rückgabewerte der Mock-Objekte
        self.character.eve_character.character_id = "123"
        mock_filter.return_value = [self.character]

        # Rufen Sie die Funktion auf
        response = fetch_memberaudit(self.request)

        # Überprüfen Sie, ob die Mock-Objekte aufgerufen wurden
        mock_get_or_create.assert_called_once_with(
            character=self.character.eve_character, id=self.character.id
        )
        mock_apply_async.assert_called_once_with(
            args=["123"], kwargs={"force_refresh": True}, priority=6
        )
        mock_info.assert_called_once()

        # Überprüfen Sie die Antwort
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ledger/index.html")
