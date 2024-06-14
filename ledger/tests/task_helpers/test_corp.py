import datetime
from unittest.mock import MagicMock, patch

import pytz

from django.test import TestCase
from django.utils import timezone
from esi.errors import TokenError
from esi.models import Token

from ledger.errors import DatabaseError
from ledger.models.corporationaudit import CorporationWalletDivision
from ledger.task_helpers.corp_helpers import (
    get_corp_token,
    update_corp_wallet_division,
    update_corp_wallet_journal,
)
from ledger.task_helpers.etag_helpers import NotModifiedError
from ledger.tests.testdata.esi_stub import esi_client_stub
from ledger.tests.testdata.load_allianceauth import load_allianceauth

MODULE_PATH = "ledger.task_helpers.corp_helpers"


class GetCorpTokenTest(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()

        cls.mock_token1 = MagicMock(spec=Token)
        cls.mock_token1.character_id = 1001
        cls.mock_token1.valid_access_token.return_value = "token"

        cls.mock_token2 = MagicMock(spec=Token)
        cls.mock_token2.character_id = 1004
        cls.mock_token2.valid_access_token.return_value = "token"

        cls.mock_token3 = MagicMock(spec=Token)
        cls.mock_token3.character_id = 1005
        cls.mock_token3.valid_access_token.return_value = "token"

    @patch(MODULE_PATH + ".EveCharacter.objects.filter")
    @patch(MODULE_PATH + ".Token.objects.filter")
    @patch(MODULE_PATH + ".esi")
    def test_get_corp_token_valid(self, mock_esi, mock_token_filter, mock_char_filter):
        # given
        mock_char_filter.return_value.values.return_value = [
            {"character_id": 1001},
            {"character_id": 1004},
            {"character_id": 1005},
        ]

        mock_tokens = [self.mock_token1, self.mock_token2, self.mock_token3]
        mock_token_filter.return_value.require_scopes.return_value = mock_tokens
        mock_esi.client = esi_client_stub

        # when
        result = get_corp_token(
            2001, ["esi-characters.read_corporation_roles.v1"], ["Factory_Manager"]
        )

        # then
        self.assertEqual(result, self.mock_token1)

    @patch(MODULE_PATH + ".EveCharacter.objects.filter")
    @patch(MODULE_PATH + ".Token.objects.filter")
    @patch(MODULE_PATH + ".esi")
    def test_get_corp_token_valid_norole_scope(
        self, mock_esi, mock_token_filter, mock_char_filter
    ):
        # given
        mock_char_filter.return_value.values.return_value = [
            {"character_id": 1001},
            {"character_id": 1004},
            {"character_id": 1005},
        ]

        mock_tokens = [self.mock_token1, self.mock_token2, self.mock_token3]
        mock_token_filter.return_value.require_scopes.return_value = mock_tokens
        mock_esi.client = esi_client_stub

        # when
        result = get_corp_token(2001, ["No Req Scope"], ["No Role"])

        # then
        self.assertFalse(result)

    @patch(MODULE_PATH + ".EveCharacter.objects.filter")
    @patch(MODULE_PATH + ".Token.objects.filter")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".logger")
    def test_get_corp_token_no_token(
        self, mock_logger, mock_esi, mock_token_filter, mock_char_filter
    ):
        # given
        mock_char_filter.return_value.values.return_value = [
            {"character_id": 1001},
            {"character_id": 1004},
            {"character_id": 1005},
        ]

        mock_tokens = [self.mock_token1, self.mock_token2, self.mock_token3]
        mock_token_filter.return_value.require_scopes.return_value = mock_tokens
        mock_esi.client.Character.get_characters_character_id_roles.side_effect = (
            TokenError()
        )

        # when
        result = get_corp_token(
            2001, ["esi-characters.read_corporation_roles.v1"], ["Factory_Manager"]
        )
        # then
        self.assertFalse(result)
        assert mock_logger.error.called


class UpdateCorpWalletDivisionTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()

        cls.mock_token = MagicMock(spec=Token)
        cls.mock_token.character_id = 1001
        cls.mock_token.corporation_id = 2001
        cls.mock_token.valid_access_token.return_value = "token"
        # TODO: Fetch from Fake ESI
        cls.journal = [
            {
                "amount": 1000,
                "balance": 2000,
                "context_id": 0,
                "context_id_type": "division",
                "date": timezone.now(),
                "description": "Test",
                "first_party_id": 1001,
                "id": 1,
                "entry_id": 1,
                "reason": "Test",
                "ref_type": "player_division",
                "second_party_id": 1002,
                "tax": 0,
                "tax_receiver_id": 0,
            },
            {
                "amount": 1000,
                "balance": 2000,
                "context_id": 0,
                "context_id_type": "division",
                "date": timezone.now(),
                "description": "Test",
                "first_party_id": 1004,
                "id": 2,
                "entry_id": 2,
                "reason": "Test",
                "ref_type": "player_division",
                "second_party_id": 1002,
                "tax": 0,
                "tax_receiver_id": 0,
            },
            {
                "amount": 1000,
                "balance": 2000,
                "context_id": 0,
                "context_id_type": "division",
                "date": timezone.now(),
                "description": "Test",
                "first_party_id": 1010,
                "entry_id": 3,
                "id": 3,
                "reason": "Test",
                "ref_type": "player_division",
                "second_party_id": 1001,
                "tax": 0,
                "tax_receiver_id": 0,
            },
            {
                "amount": 1000,
                "balance": 2000,
                "context_id": 0,
                "context_id_type": "division",
                "date": timezone.now(),
                "description": "Test",
                "first_party_id": 1001,
                "entry_id": 4,
                "id": 4,
                "reason": "Test",
                "ref_type": "player_division",
                "second_party_id": 1101,
                "tax": 0,
                "tax_receiver_id": 0,
            },
        ]

    @patch(MODULE_PATH + ".CorporationAudit.objects.get")
    @patch(MODULE_PATH + ".get_corp_token")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".CorporationWalletDivision.objects.update_or_create")
    @patch(MODULE_PATH + ".update_corp_wallet_journal")
    def test_update_corp_wallet_division(
        self,
        _,
        mock_update_or_create,
        mock_etag_results,
        mock_esi,
        mock_get_token,
        mock_get_corp,
    ):
        # given
        mock_get_corp.return_value = MagicMock()
        mock_get_corp.return_value.corporation.corporation_id = 2001
        mock_get_token.return_value = self.mock_token
        mock_etag_results.return_value = [{"division": 1, "balance": 100}]
        mock_update_or_create.return_value = (MagicMock(), True)
        mock_esi.client = esi_client_stub
        # when
        result = update_corp_wallet_division(2001)
        # then
        self.assertEqual(
            result,
            (
                "Finished wallet divs for: %s",
                mock_get_corp.return_value.corporation.corporation_name,
            ),
        )

    @patch(MODULE_PATH + ".CorporationAudit.objects.get")
    @patch(MODULE_PATH + ".get_corp_token")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".CorporationWalletDivision.objects.update_or_create")
    @patch(MODULE_PATH + ".update_corp_wallet_journal")
    def test_update_corp_wallet_division_no_division_item(
        self,
        _,
        mock_update_or_create,
        mock_etag_results,
        mock_esi,
        mock_get_token,
        mock_get_corp,
    ):
        # given
        mock_get_corp.return_value = MagicMock()
        mock_get_corp.return_value.corporation.corporation_id = 2001
        mock_get_token.return_value = self.mock_token
        mock_etag_results.return_value = [{"division": 1, "balance": 100}]
        mock_update_or_create.return_value = (None, False)
        mock_esi.client = esi_client_stub
        # when
        result = update_corp_wallet_division(2001)
        # then
        self.assertEqual(
            result,
            (
                "Finished wallet divs for: %s",
                mock_get_corp.return_value.corporation.corporation_name,
            ),
        )

    @patch(MODULE_PATH + ".CorporationAudit.objects.get")
    @patch(MODULE_PATH + ".get_corp_token")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".CorporationWalletDivision.objects.update_or_create")
    @patch(MODULE_PATH + ".update_corp_wallet_journal")
    def test_update_corp_wallet_division_no_token(
        self,
        _,
        mock_update_or_create,
        mock_etag_results,
        mock_esi,
        mock_get_token,
        mock_get_corp,
    ):
        # given
        mock_get_corp.return_value = MagicMock()
        mock_get_corp.return_value.corporation.corporation_id = 2001
        mock_get_token.return_value = None
        mock_etag_results.return_value = [{"division": 1, "balance": 100}]
        mock_update_or_create.return_value = (MagicMock(), True)
        mock_esi.client = esi_client_stub
        # when
        result = update_corp_wallet_division(2001)
        # then
        self.assertEqual(result, "No Tokens")

    @patch(MODULE_PATH + ".CorporationAudit.objects.get")
    @patch(MODULE_PATH + ".get_corp_token")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".CorporationWalletDivision.objects.update_or_create")
    @patch(MODULE_PATH + ".update_corp_wallet_journal")
    @patch(MODULE_PATH + ".logger")
    def test_update_corp_wallet_division_not_modified(
        self,
        mock_logger,
        _,
        mock_update_or_create,
        mock_etag_results,
        mock_esi,
        mock_get_token,
        mock_get_corp,
    ):
        # given
        mock_get_corp.return_value = MagicMock()
        mock_get_corp.return_value.corporation.corporation_id = 2001
        mock_get_token.return_value = self.mock_token
        mock_etag_results.side_effect = NotModifiedError()
        mock_update_or_create.return_value = (MagicMock(), True)
        mock_esi.client = esi_client_stub
        # when
        result = update_corp_wallet_division(2001)
        # then
        self.assertEqual(
            result,
            (
                "Finished wallet divs for: %s",
                mock_get_corp.return_value.corporation.corporation_name,
            ),
        )
        mock_logger.debug.assert_called_once_with(
            "No New wallet data for: %s",
            mock_get_corp.return_value.corporation.corporation_name,
        )

    @patch(MODULE_PATH + ".get_corp_token")
    @patch(MODULE_PATH + ".CorporationAudit.objects.get")
    @patch(MODULE_PATH + ".CorporationWalletDivision.objects.get")
    @patch(MODULE_PATH + ".CorporationWalletJournalEntry.objects.filter")
    @patch(MODULE_PATH + ".EveEntity.objects.all")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".EveEntity.objects.create_bulk_from_esi")
    @patch(MODULE_PATH + ".CorporationWalletJournalEntry.objects.bulk_create")
    def test_update_corp_wallet_journal_success(
        self,
        mock_bulk_create,
        mock_create_bulk_from_esi,
        mock_etag_results,
        mock_esi,
        mock_all,
        mock_filter,
        mock_division_get,
        mock_audit_get,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token

        mock_audit_get.return_value = MagicMock()
        mock_audit_get.return_value.corporation.corporation_id = 2001

        mock_division_get.return_value = CorporationWalletDivision(
            name=None, balance=1000.00, division=1
        )

        mock_filter.return_value.order_by.return_value.values_list.return_value = [1, 3]

        mock_all.return_value.values_list.return_value = []

        mock_esi.client = esi_client_stub

        date_string = "2016-10-29T14:00:00Z"
        date_object = datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
        date_object = date_object.replace(tzinfo=pytz.UTC)

        mock_etag_results.return_value = self.journal

        mock_create_bulk_from_esi.return_value = True
        mock_bulk_create.return_value = [MagicMock()]

        # when
        result = update_corp_wallet_journal(2001, 1)

        # then
        self.assertEqual(result, True)

    @patch(MODULE_PATH + ".get_corp_token")
    @patch(MODULE_PATH + ".CorporationAudit.objects.get")
    @patch(MODULE_PATH + ".CorporationWalletDivision.objects.get")
    def test_update_corp_wallet_journal_no_token(
        self, mock_division_get, mock_audit_get, mock_get_token
    ):
        # given
        mock_get_token.return_value = None
        mock_audit_get.return_value = MagicMock()
        mock_division_get.return_value = MagicMock()

        # when
        result = update_corp_wallet_journal(2001, 1)

        # then
        self.assertEqual(result, "No Tokens")

    @patch(MODULE_PATH + ".get_corp_token")
    @patch(MODULE_PATH + ".CorporationAudit.objects.get")
    @patch(MODULE_PATH + ".CorporationWalletDivision.objects.get")
    @patch(MODULE_PATH + ".CorporationWalletJournalEntry.objects.filter")
    @patch(MODULE_PATH + ".EveEntity.objects.all")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".logger")
    def test_update_corp_wallet_journal_not_modified(
        self,
        mock_logger,
        mock_etag_results,
        mock_esi,
        mock_all,
        mock_filter,
        mock_division_get,
        mock_audit_get,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token

        mock_audit_get.return_value = MagicMock()
        mock_audit_get.return_value.corporation.corporation_id = 2001

        mock_division_get.return_value = CorporationWalletDivision(
            name=None, balance=1000.00, division=1
        )

        mock_filter.return_value.order_by.return_value.values_list.return_value = []

        mock_all.return_value.values_list.return_value = []

        mock_esi.client = esi_client_stub

        date_string = "2016-10-29T14:00:00Z"
        date_object = datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
        date_object = date_object.replace(tzinfo=pytz.UTC)

        mock_etag_results.side_effect = NotModifiedError()

        # when
        result = update_corp_wallet_journal(2001, 1)

        # then
        self.assertEqual(result, True)
        mock_logger.debug.assert_called_with(
            "No New wallet data for: Div: %s Corp: %s",
            mock_audit_get.return_value.corporation.corporation_name,
            1,
        )

    @patch(MODULE_PATH + ".get_corp_token")
    @patch(MODULE_PATH + ".CorporationAudit.objects.get")
    @patch(MODULE_PATH + ".CorporationWalletDivision.objects.get")
    @patch(MODULE_PATH + ".CorporationWalletJournalEntry.objects.filter")
    @patch(MODULE_PATH + ".EveEntity.objects.all")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".EveEntity.objects.create_bulk_from_esi")
    def test_update_corp_wallet_journal_raise_db(
        self,
        mock_create_bulk_from_esi,
        mock_etag_results,
        mock_esi,
        mock_all,
        mock_filter,
        mock_division_get,
        mock_audit_get,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token

        mock_audit_get.return_value = MagicMock()
        mock_audit_get.return_value.corporation.corporation_id = 2001

        mock_division_get.return_value = CorporationWalletDivision(
            name=None, balance=1000.00, division=1
        )

        mock_filter.return_value.order_by.return_value.values_list.return_value = []

        mock_all.return_value.values_list.return_value = []

        mock_esi.client = esi_client_stub

        date_string = "2016-10-29T14:00:00Z"
        date_object = datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
        date_object = date_object.replace(tzinfo=pytz.UTC)

        mock_etag_results.return_value = self.journal

        mock_create_bulk_from_esi.return_value = None  # No names created

        # when
        with self.assertRaises(DatabaseError):
            result = update_corp_wallet_journal(2001, 1)

            # then
            self.assertEqual(result, True)
