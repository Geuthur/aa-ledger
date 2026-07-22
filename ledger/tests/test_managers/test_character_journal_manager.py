# Standard Library
from http import HTTPStatus
from unittest.mock import MagicMock, patch

# Third Party
import pook

# Django
from django.utils import timezone

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CharacterJournalFactory,
    CharacterOwnerFactory,
    EveEntityFactory,
)

MODULE_PATH = "ledger.managers.character_journal_manager"


@patch("ledger.models.general.EveEntity")
class TestCharacterJournalManager(LedgerTestCase):
    """Test Character Journal Manager for Character."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CharacterOwnerFactory(user=cls.user)
        cls.token = cls.user.token_set.first()
        cls.audit.get_token = MagicMock(return_value=cls.token)

    @pook.on
    def test_update_wallet_journal(self, mock_eveentity):
        """
        Test updating the wallet journal for a character.

        This test mocks the ESI client and EveEntity model to simulate
        fetching wallet journal entries from ESI and updating the local
        database accordingly.

        ### Results:
            - Wallet Journal Entries (entry_id: 10, 13, 16) are created with correct data.
        """
        # Test Data
        EveEntityFactory(eve_id=1001)
        EveEntityFactory(eve_id=1002)
        EveEntityFactory(eve_id=2001)
        pook.get(
            f"https://esi.evetech.net/characters/{self.user_character.character_id}/wallet/journal",
            reply=HTTPStatus.OK,
            response_headers={"X-Pages": "1"},
            response_json=[
                {
                    "amount": 1000,
                    "balance": 2000,
                    "context_id": 1,
                    "context_id_type": "character_id",
                    "date": "2016-10-29T14:00:00Z",
                    "description": "Test Journal",
                    "first_party_id": 1001,
                    "id": 10,
                    "reason": "Test Reason",
                    "ref_type": "player_donation",
                    "second_party_id": 1002,
                    "tax": 0,
                    "tax_receiver_id": 0,
                },
                {
                    "amount": 5000,
                    "balance": 10000,
                    "context_id": 2,
                    "context_id_type": "character_id",
                    "date": "2016-12-01T14:00:00Z",
                    "description": "Courier Contract",
                    "first_party_id": 2001,
                    "id": 13,
                    "reason": "Courier has been completed",
                    "ref_type": "contract_reward",
                    "second_party_id": 1001,
                    "tax": 0,
                    "tax_receiver_id": 0,
                },
                {
                    "amount": 10000,
                    "balance": 20000,
                    "context_id": 4,
                    "context_id_type": "character_id",
                    "date": "2016-12-01T14:00:00Z",
                    "description": "Unknown Second Party",
                    "first_party_id": 1001,
                    "id": 16,
                    "reason": "Second party unknown",
                    "ref_type": "bounty_prizes",
                    "second_party_id": 9999,
                    "tax": 0,
                    "tax_receiver_id": 0,
                },
            ],
        )

        mock_eveentity.objects.create_bulk_from_esi.return_value = True

        EveEntity.objects.create(
            eve_id=9999, name="Test Character 1", category="character"
        )

        # Test Action
        self.audit.update_wallet_journal(force_refresh=False)

        # Expected Results
        self.assertSetEqual(
            set(self.audit.ledger_character_journal.values_list("entry_id", flat=True)),
            {10, 13, 16},
        )
        obj = self.audit.ledger_character_journal.get(entry_id=10)
        self.assertEqual(obj.amount, 1000)
        self.assertEqual(obj.context_id, 1)
        self.assertEqual(obj.first_party.eve_id, 1001)
        self.assertEqual(obj.second_party.eve_id, 1002)

        obj = self.audit.ledger_character_journal.get(entry_id=13)
        self.assertEqual(obj.amount, 5000)

        obj = self.audit.ledger_character_journal.get(entry_id=16)
        self.assertEqual(obj.amount, 10000)


class TestCharacterJournalManagerAnnotations(LedgerTestCase):
    """Test annotation methods in CharacterJournalManager."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal_entry = CharacterJournalFactory(
            amount=1000,
            ref_type="player_donation",
        )

    def test_annotate_bounty_income(self):
        """ "Test annotating bounty income."""
        qs = (
            self.journal_entry.character.ledger_character_journal.all().annotate_bounty_income()
        )
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "bounty_income"),
                "Bounty income annotation should be present",
            )
            self.assertEqual(obj.bounty_income, 0)

    def test_annotate_miscellaneous_income(self):
        """Test annotating miscellaneous income."""
        qs = (
            self.journal_entry.character.ledger_character_journal.all().annotate_miscellaneous()
        )
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "miscellaneous"),
                "Miscellaneous income annotation should be present",
            )
            self.assertEqual(obj.miscellaneous, 1000.00)


class TestCharacterJournalManagerAggregate(LedgerTestCase):
    """Test aggregation methods in CharacterJournalManager."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal_entry = CharacterJournalFactory(
            amount=1000,
            ref_type="player_donation",
        )

    def test_aggregate_bounty(self):
        """Test aggregating bounty income."""
        result = (
            self.journal_entry.character.ledger_character_journal.all().aggregate_bounty()
        )
        self.assertEqual(result, 0)

    def test_aggregate_costs(self):
        """Test aggregating costs."""
        result = (
            self.journal_entry.character.ledger_character_journal.all().aggregate_costs()
        )
        self.assertEqual(result, 0)

    def test_aggregate_miscellaneous(self):
        """Test aggregating miscellaneous income."""
        result = (
            self.journal_entry.character.ledger_character_journal.all().aggregate_miscellaneous()
        )
        self.assertEqual(result, 1000.00)

    def test_aggregate_ref_type(self):
        """Test aggregating by reference type."""
        result = self.journal_entry.character.ledger_character_journal.all().aggregate_ref_type(
            ref_type=["player_donation"], income=True
        )
        self.assertEqual(result, 1000.00)
