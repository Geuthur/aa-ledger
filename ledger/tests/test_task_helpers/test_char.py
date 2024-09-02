from datetime import datetime
from unittest.mock import MagicMock, patch

import _strptime
from bravado.exception import HTTPNotModified

from django.test import TestCase
from esi.errors import TokenError
from esi.models import Token

from ledger.task_helpers.char_helpers import (
    update_character_mining,
    update_character_wallet,
)
from ledger.task_helpers.etag_helpers import NotModifiedError
from ledger.tests.testdata.esi_stub import esi_client_stub
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all

MODULE_PATH = "ledger.task_helpers.char_helpers"


class TestCharacterHelpers(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()

        cls.mock_token = MagicMock(spec=Token)
        cls.mock_token.character_id = 1001
        cls.mock_token.valid_access_token.return_value = "token"

        cls.journal = [
            {
                "entry_id": 1,
                "amount": 1000,
                "balance": 2000,
                "context_id": 0,
                "context_id_type": "division",
                "date": "2016-10-29T14:00:00Z",
                "description": "Test",
                "first_party_id": 1001,
                "id": 1,
                "reason": "Test",
                "ref_type": "player_division",
                "second_party_id": 1002,
                "tax": 0,
                "tax_receiver_id": 0,
            },
            {
                "entry_id": 2,
                "amount": 1000,
                "balance": 3000,
                "context_id": 0,
                "context_id_type": "division",
                "date": "2016-10-29T14:00:00Z",
                "description": "Test",
                "first_party_id": 1010,
                "id": 2,
                "reason": "Test",
                "ref_type": "player_division",
                "second_party_id": 1020,
                "tax": 0,
                "tax_receiver_id": 0,
            },
            {
                "entry_id": 5,
                "amount": 1000,
                "balance": 4000,
                "context_id": 0,
                "context_id_type": "division",
                "date": "2016-10-29T14:00:00Z",
                "description": "Test",
                "first_party_id": 1035,
                "id": 5,
                "reason": "Test",
                "ref_type": "player_division",
                "second_party_id": 1034,
                "tax": 0,
                "tax_receiver_id": 0,
            },
            {
                "entry_id": 6,
                "amount": 1000,
                "balance": 4000,
                "context_id": 0,
                "context_id_type": "division",
                "date": "2016-10-29T14:00:00Z",
                "description": "Test",
                "first_party_id": 1001,
                "id": 6,
                "reason": "Test",
                "ref_type": "player_division",
                "second_party_id": 1002,
                "tax": 0,
                "tax_receiver_id": 0,
            },
        ]

        cls.mining = [
            {
                "date": datetime.strptime("2024-03-16", "%Y-%m-%d"),
                "quantity": 16751,
                "solar_system_id": 30004783,
                "type_id": 17425,
            },
            {
                "date": datetime.strptime("2024-03-16", "%Y-%m-%d"),
                "quantity": 20000,
                "solar_system_id": 30004783,
                "type_id": 17425,
            },
            {
                "date": datetime.strptime("2024-03-16", "%Y-%m-%d"),
                "quantity": 9810,
                "solar_system_id": 30004783,
                "type_id": 17428,
            },
            {
                "date": datetime.strptime("2024-03-22", "%Y-%m-%d"),
                "quantity": 12550,
                "solar_system_id": 30004783,
                "type_id": 17425,
            },
        ]

        cls.mining2 = [
            {
                "date": datetime.strptime("2024-03-16", "%Y-%m-%d"),
                "quantity": 16751,
                "solar_system_id": 30004783,
                "type_id": 17425,
            },
        ]

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".CharacterWalletJournalEntry.objects")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".EveEntity.objects.all")
    @patch(MODULE_PATH + ".EveEntity.objects.create_bulk_from_esi")
    @patch(MODULE_PATH + ".CharacterWalletJournalEntry.objects.bulk_create")
    def test_update_character_wallet(
        self,
        mock_charjournal_bulk,
        mock_create_names,
        mock_entity,
        mock_etag,
        mock_esi,
        mock_journal,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client = esi_client_stub
        # TODO get Data from Test ESI
        # mock_etag.return_value = mock_esi.client.Wallet.get_characters_character_id_wallet_journal(character_id=1001)
        mock_etag.return_value = self.journal
        mock_journal.filter.return_value.values_list.return_value = [
            1,
            3,
        ]
        mock_entity.return_value.values_list.return_value = [1001]
        mock_create_names.return_value = True
        mock_charjournal_bulk.return_value = None
        # when
        result = update_character_wallet(1001)
        # then
        self.assertEqual(result, ("Finished wallet transactions for: %s", "Gneuten"))

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".CharacterWalletJournalEntry.objects")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".EveEntity.objects.all")
    @patch(MODULE_PATH + ".EveEntity.objects.create_bulk_from_esi")
    @patch(MODULE_PATH + ".CharacterWalletJournalEntry.objects.bulk_create")
    def test_update_character_wallet_token_error(
        self,
        mock_charjournal_bulk,
        mock_create_names,
        mock_entity,
        mock_etag,
        mock_esi,
        mock_journal,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client = esi_client_stub
        mock_etag.return_value = self.journal
        mock_journal.filter.return_value.values_list.return_value = [
            1,
            3,
        ]
        mock_entity.return_value.values_list.return_value = [1001, 1002, 1003]
        mock_create_names.return_value = False
        mock_charjournal_bulk.return_value = None
        # when
        # then
        with self.assertRaises(TokenError):
            update_character_wallet(1001)

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".logger")
    @patch(MODULE_PATH + ".etag_results")
    def test_update_character_wallet_not_modified(
        self, mock_etag, mock_logger, mock_get_token
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_etag.side_effect = NotModifiedError
        # when
        update_character_wallet(1001)
        # then
        mock_logger.debug.assert_called_with("No New wallet data for: %s", "Gneuten")

    @patch(MODULE_PATH + ".get_token")
    def test_update_character_wallet_no_token(self, mock_get_token):
        # given
        mock_get_token.return_value = None
        # when
        result = update_character_wallet(1001)
        # then
        self.assertEqual(result, ("No Tokens"))

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".CharacterMiningLedger.objects")
    @patch(MODULE_PATH + ".EveType.objects.bulk_get_or_create_esi")
    def test_update_character_mining(
        self, _, mock_existing, mock_etag, mock_esi, mock_get_token
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client = esi_client_stub
        mock_etag.return_value = self.mining
        mock_existing.filter.return_value.values_list.return_value = [
            "20240316-17425-1001-30004783"
        ]
        # when
        result = update_character_mining(1001)
        # then
        self.assertEqual(result, ("Finished Mining for: Gneuten"))

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".CharacterMiningLedger.objects")
    @patch(MODULE_PATH + ".EveType.objects.bulk_get_or_create_esi")
    def test_update_character_mining_non_existing(
        self, _, mock_existing, mock_etag, mock_esi, mock_get_token
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client = esi_client_stub
        mock_etag.return_value = self.mining
        mock_existing.filter.return_value.values_list.return_value = []
        # when
        result = update_character_mining(1001)
        # then
        self.assertEqual(result, ("Finished Mining for: Gneuten"))

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".CharacterMiningLedger.objects")
    @patch(MODULE_PATH + ".EveType.objects.bulk_get_or_create_esi")
    def test_update_character_mining_2(
        self, _, mock_existing, mock_etag, mock_esi, mock_get_token
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_esi.client = esi_client_stub
        mock_etag.return_value = self.mining2
        mock_existing.filter.return_value.values_list.return_value = [
            "20240316-17425-1001-30004783"
        ]
        # when
        result = update_character_mining(1001)
        # then
        self.assertEqual(result, ("Finished Mining for: Gneuten"))

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".etag_results")
    def test_update_character_mining_no_token(self, _, mock_esi, mock_get_token):
        # given
        mock_get_token.return_value = None
        # when
        result = update_character_mining(1001)
        # then
        self.assertEqual(result, ("No Tokens"))

    @patch(MODULE_PATH + ".get_token")
    @patch(MODULE_PATH + ".logger")
    @patch(MODULE_PATH + ".etag_results")
    @patch(MODULE_PATH + ".esi.client.Industry.get_characters_character_id_mining")
    def test_update_character_mining_not_modified(
        self,
        mock_get_characters_character_id_mining,
        mock_etag,
        mock_logger,
        mock_get_token,
    ):
        # given
        mock_get_token.return_value = self.mock_token
        mock_etag.side_effect = NotModifiedError
        mock_get_characters_character_id_mining.side_effect = HTTPNotModified
        # when
        update_character_mining(1001)
        # then
        mock_logger.debug.assert_called_with("No New Mining for: %s", "Gneuten")
