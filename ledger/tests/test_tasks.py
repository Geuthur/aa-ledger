from datetime import timedelta
from unittest.mock import MagicMock, call, patch

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from esi.errors import TokenExpiredError

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import create_user_from_evecharacter

from ledger.models.characteraudit import CharacterAudit
from ledger.models.corporationaudit import CorporationAudit
from ledger.tasks import (
    create_member_audit,
    create_missing_character,
    update_all_characters,
    update_all_corps,
    update_char_mining_ledger,
    update_char_wallet,
    update_character,
    update_corp,
    update_corp_wallet,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all

MODULE_PATH = "ledger.tasks"


class TestTasks(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
                "ledger.admin_access",
                "ledger.corp_audit_admin_manager",
                "ledger.corp_audit_admin_manager",
            ],
        )
        cls.token = cls.user.token_set.first()
        cls.corporation = cls.character_ownership.character.corporation

    @patch(MODULE_PATH + ".EveCharacter.objects.create_character")
    def test_create_character(self, _):
        # given
        chars_list = [1010, 1011]
        # when
        result = create_missing_character(chars_list=chars_list)
        # then
        self.assertTrue(result)

    @patch(MODULE_PATH + ".CharacterAudit.objects.update_or_create")
    @patch(MODULE_PATH + ".EveCharacter.objects.get_character_by_id")
    @patch("memberaudit.models.Character.objects.all")
    @patch(MODULE_PATH + ".CharacterAudit.objects.all")
    def test_create_member_audit(
        self,
        mock_char_audit_all,
        mock_char_all,
        mock_get_character_by_id,
        mock_update_or_create,
    ):
        # Setup mock return values
        mock_char_audit_all.return_value.values_list.return_value = []
        mock_char_all.return_value.values_list.return_value = [1999]
        mock_get_character_by_id.return_value = EveCharacter(
            character_id=1999,
            character_name="Test Character",
            corporation_id=2001,
            corporation_name="Hell Rider'Z",
        )

        # Call the function
        create_member_audit()

        # Check that update_or_create was called
        mock_update_or_create.assert_called_once()

    @patch(MODULE_PATH + ".CharacterAudit.objects.update_or_create")
    @patch(MODULE_PATH + ".EveCharacter.objects.get_character_by_id")
    @patch("memberaudit.models.Character.objects.all")
    @patch(MODULE_PATH + ".CharacterAudit.objects.all")
    def test_create_member_audit_no_update_or_create(
        self,
        mock_char_audit_all,
        mock_char_all,
        mock_get_character_by_id,
        mock_update_or_create,
    ):
        # Setup mock return values
        mock_char_audit_all.return_value.values_list.return_value = [1, 2, 3, 4, 5]
        mock_char_all.return_value.values_list.return_value = [2, 3, 4, 5]

        # Call the function
        create_member_audit()

        # Check that update_or_create was not called
        mock_update_or_create.assert_not_called()

    @patch(MODULE_PATH + ".CharacterAudit.objects.update_or_create")
    @patch(MODULE_PATH + ".EveCharacter.objects.get_character_by_id")
    @patch("memberaudit.models.Character.objects.all")
    @patch(MODULE_PATH + ".CharacterAudit.objects.all")
    def test_create_member_audit_integrityerror(
        self,
        mock_char_audit_all,
        mock_char_all,
        mock_get_character_by_id,
        mock_update_or_create,
    ):
        # Setup mock return values
        mock_char_audit_all.return_value.values_list.return_value = [1, 2, 3, 4, 5]
        mock_char_all.return_value.values_list.return_value = [2, 3, 4, 5]
        mock_update_or_create.side_effect = IntegrityError("duplicate key")
        # Call the function
        create_member_audit()

        # Check that update_or_create was not called
        mock_update_or_create.assert_not_called()

    @patch(MODULE_PATH + ".EveCharacter.objects.create_character")
    def test_create_character_integrity(self, mock_character):
        # given
        chars_list = [1001, 1011]
        mock_character.side_effect = [IntegrityError("duplicate key"), None]
        # when
        result = create_missing_character(chars_list=chars_list)
        # then
        self.assertTrue(result)

    @patch(MODULE_PATH + ".update_character.apply_async")
    @patch(MODULE_PATH + ".logger")
    def test_update_all_characters(self, mock_logger, mock_update_character):
        # given
        characters_count = CharacterAudit.objects.count()
        # when
        update_all_characters()
        # then
        self.assertEqual(mock_update_character.call_count, characters_count)
        mock_logger.info.assert_called_once_with(
            "Queued %s Char Audit Updates", characters_count
        )

    @patch(MODULE_PATH + ".CharacterAudit.objects.select_related")
    def test_update_character(self, mock_select_related):
        # given
        mock_character = MagicMock()
        mock_character.last_update_mining = timezone.now()
        mock_character.last_update_wallet = timezone.now()
        mock_character.character = MagicMock()
        mock_character.character.character_id = self.token.character_id
        mock_character.character.character_name = self.token.character_name

        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_character
        mock_select_related.return_value.filter.return_value = mock_filter
        # when
        result = update_character(self.token.character_id)
        # then
        self.assertTrue(result)

    @patch(MODULE_PATH + ".update_character_mining")
    def test_update_character_mining(self, mock_char_mining):
        # given
        expected_return_value = f"Finished Mining for: {self.token.character_name}"
        mock_char_mining.return_value = expected_return_value
        # when
        result = update_char_mining_ledger(self.token.character_id)
        # then
        self.assertTrue(mock_char_mining.called)
        self.assertEqual(expected_return_value, result)

    @patch(MODULE_PATH + ".update_character_wallet")
    def test_update_character_wallet(self, mock_char_wallet):
        # given
        expected_return_value = (
            f"Finished wallet transactions for: {self.token.character_name}"
        )
        mock_char_wallet.return_value = expected_return_value
        # when
        result = update_char_wallet(self.token.character_id)
        # then
        self.assertTrue(mock_char_wallet.called)
        self.assertEqual(expected_return_value, result)

    @patch(MODULE_PATH + ".update_char_mining_ledger.si")
    @patch(MODULE_PATH + ".update_char_wallet.si")
    @patch(MODULE_PATH + ".Token.get_token")
    @patch(MODULE_PATH + ".EveCharacter.objects.get_character_by_id")
    @patch(MODULE_PATH + ".CharacterAudit.objects.update_or_create")
    @patch(MODULE_PATH + ".CharacterAudit.objects.select_related")
    def test_update_character_from_token(
        self,
        mock_check_char,
        mock_update_or_create,
        mock_get_character_by_id,
        mock_get_token,
        mock_char_wallet,
        mock_char_mining,
    ):
        # given
        mock_check_char.return_value.filter.return_value.first.return_value = None
        mock_token = MagicMock()
        mock_token.valid_access_token.return_value = True
        mock_get_token.return_value = mock_token
        mock_character = MagicMock()
        mock_character.last_update_mining = timezone.now() - timedelta(days=1)
        mock_character.last_update_wallet = timezone.now() - timedelta(days=1)
        mock_update_or_create.return_value = (mock_character, True)
        # when
        update_character(self.token.character_id)
        # then
        mock_get_token.assert_called_once_with(
            self.token.character_id, CharacterAudit.get_esi_scopes()
        )
        mock_token.valid_access_token.assert_called_once()
        mock_get_character_by_id.assert_called_once_with(mock_token.character_id)
        mock_update_or_create.assert_called_once()
        self.assertTrue(mock_char_wallet.called)
        self.assertTrue(mock_char_mining.called)

    @patch(MODULE_PATH + ".Token.get_token")
    @patch(MODULE_PATH + ".CharacterAudit.objects.update_or_create")
    @patch(MODULE_PATH + ".CharacterAudit.objects.select_related")
    def test_update_character_token_expired_token(
        self, mock_check_char, mock_update_or_create, mock_get_token
    ):
        # given
        mock_check_char.return_value.filter.return_value.first.return_value = None
        mock_token = MagicMock()
        mock_token.valid_access_token.side_effect = TokenExpiredError
        mock_get_token.return_value = mock_token
        mock_character = MagicMock()
        mock_update_or_create.return_value = (mock_character, True)
        # when
        result = update_character(self.token.character_id)
        # then
        self.assertFalse(result)
        mock_get_token.assert_called_once_with(
            self.token.character_id, CharacterAudit.get_esi_scopes()
        )
        mock_token.valid_access_token.assert_called_once()

    @patch(MODULE_PATH + ".Token.get_token")
    @patch(MODULE_PATH + ".CharacterAudit.objects.select_related")
    def test_update_character_token_no_access_token(
        self, mock_check_char, mock_get_token
    ):
        # given
        mock_check_char.return_value.filter.return_value.first.return_value = None
        mock_token = MagicMock()
        mock_token.valid_access_token.return_value = False
        mock_get_token.return_value = mock_token
        # when
        result = update_character(self.token.character_id)
        # then
        mock_token.valid_access_token.assert_called_once()
        self.assertFalse(result)

    @patch(MODULE_PATH + ".Token.get_token")
    @patch(MODULE_PATH + ".CharacterAudit.objects.select_related")
    @patch(MODULE_PATH + ".logger")
    def test_update_character_token_no_token(
        self, mock_logger, mock_check_char, mock_get_token
    ):
        # given
        mock_check_char.return_value.filter.return_value.first.return_value = None
        mock_get_token.return_value = False
        # when
        result = update_character(self.token.character_id)
        # then
        self.assertFalse(result)
        mock_logger.info.assert_called_once_with("No Tokens for %s", 1001)

    @patch(MODULE_PATH + ".update_corp.apply_async")
    @patch(MODULE_PATH + ".logger")
    def test_update_all_cors(self, mock_logger, mock_update_character):
        # given
        corporation_count = CorporationAudit.objects.count()
        # when
        update_all_corps()
        # then
        self.assertEqual(mock_update_character.call_count, corporation_count)
        mock_logger.info.assert_called_once_with(
            "Queued %s Corp Audit Updates", corporation_count
        )

    @patch(MODULE_PATH + ".update_corp_wallet.si")
    def test_update_corp(self, mock_corp_wallet):
        # when
        update_corp(self.corporation.corporation_id)
        # then
        self.assertTrue(mock_corp_wallet.called)

    @patch(MODULE_PATH + ".update_corp_wallet_division")
    def test_update_corp_wallet(self, mock_corp_wallet_division):
        # given
        expected_return_value = (
            f"Finished wallet divs for: {self.corporation.corporation_name}"
        )
        mock_corp_wallet_division.return_value = expected_return_value
        # when
        result = update_corp_wallet(self.corporation.corporation_id)
        # then
        self.assertTrue(mock_corp_wallet_division.called)
        self.assertEqual(expected_return_value, result)
