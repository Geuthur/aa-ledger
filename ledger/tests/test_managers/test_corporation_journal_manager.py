# Standard Library
from http import HTTPStatus
from unittest.mock import MagicMock, patch

# Third Party
import pook

# Django
from django.utils import timezone

# Alliance Auth
from esi.errors import TokenError

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CorporationJournalFactory,
    CorporationOwnerFactory,
    DivisionFactory,
    EveEntityFactory,
)
from ledger.tests.testdata.utils import (
    add_new_token,
)

MODULE_PATH = "ledger.managers.corporation_journal_manager"


class TestCorporationJournalManager(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CorporationOwnerFactory(user=cls.user)
        cls.token = add_new_token(
            user=cls.user,
            character=cls.user_character,
            scopes=cls.audit.get_esi_scopes(),
        )
        cls.audit.get_token = MagicMock(return_value=cls.token)
        cls.division = DivisionFactory(
            corporation=cls.audit, name="MEGA KONTO", balance=1000000, division_id=1
        )

    @pook.on
    @patch(MODULE_PATH + ".EveEntity")
    def test_update_wallet_journal(self, mock_eveentity):
        """
        Test updating the wallet journal for a corporation.

        This test verifies that the wallet journal entries for a corporation division
        are correctly updated from ESI data.

        ### Expected Result
        - Wallet journal entries are updated correctly.
        - Entries have correct amounts and parties.
        """
        # Test Data
        EveEntityFactory(eve_id=2001)
        EveEntityFactory(eve_id=1001)
        pook.get(
            url=f"https://esi.evetech.net/corporations/{self.audit.eve_corporation.corporation_id}/wallets/1/journal",
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
                    "first_party_id": 2001,
                    "id": 10,
                    "reason": "Test Reason",
                    "ref_type": "player_donation",
                    "second_party_id": 1001,
                    "tax": 0,
                    "tax_receiver_id": 0,
                },
                {
                    "amount": 5000,
                    "balance": 10000,
                    "context_id": 2,
                    "context_id_type": "system_id",
                    "date": "2016-12-01T14:00:00Z",
                    "description": "Bounty Tax",
                    "first_party_id": 1001,
                    "id": 13,
                    "reason": "Bounty",
                    "ref_type": "bounty_prizes",
                    "second_party_id": 2001,
                    "tax": 0,
                    "tax_receiver_id": 0,
                },
                {
                    "amount": 10000,
                    "balance": 20000,
                    "context_id": 4,
                    "context_id_type": "system_id",
                    "date": "2016-12-01T14:00:00Z",
                    "description": "Unknown Second Party",
                    "first_party_id": 1001,
                    "id": 16,
                    "reason": "Second party unknown",
                    "ref_type": "bounty_prizes",
                    "second_party_id": 9998,
                    "tax": 0,
                    "tax_receiver_id": 0,
                },
            ],
        )

        mock_eveentity.objects.create_bulk_from_esi.return_value = True

        EveEntity.objects.create(
            eve_id=9998, name="Test Character 2", category="character"
        )

        # Test Action
        self.audit.update_wallet_journal(force_refresh=False)

        # Expected Results
        self.assertSetEqual(
            set(
                self.division.ledger_corporation_journal.values_list(
                    "entry_id", flat=True
                )
            ),
            {10, 13, 16},
        )
        obj = self.division.ledger_corporation_journal.get(entry_id=10)
        self.assertEqual(obj.amount, 1000)
        self.assertEqual(obj.context_id, 1)
        self.assertEqual(obj.first_party.eve_id, 2001)
        self.assertEqual(obj.second_party.eve_id, 1001)

        obj = self.division.ledger_corporation_journal.get(entry_id=13)
        self.assertEqual(obj.amount, 5000)

        obj = self.division.ledger_corporation_journal.get(entry_id=16)
        self.assertEqual(obj.amount, 10000)

    def test_update_wallet_journal_no_token(self):
        """
        Test updating the wallet journal for a corporation when no valid token is available.

        This test verifies that a TokenError is raised when attempting to update the wallet journal
        without a valid token.

        ### Expected Result
        - A TokenError is raised indicating that no valid token was found.
        """
        # Test Data
        # Simulate no valid token by returning None
        self.audit.get_token = MagicMock(return_value=None)

        # Test Action and Expected Result
        with self.assertRaises(TokenError) as context:
            self.audit.update_wallet_journal(force_refresh=False)

        self.assertIn("No valid token found for corporation", str(context.exception))


class TestCorporationJournalManagerAnnotations(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal_entry = CorporationJournalFactory(
            amount=1000,
            date=timezone.datetime.replace(
                timezone.now(),
                year=2016,
                month=10,
                day=29,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
            ref_type="player_donation",
        )

    def test_annotate_bounty_income(self):
        qs = (
            self.journal_entry.division.ledger_corporation_journal.annotate_bounty_income()
        )
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "bounty_income"),
                "Bounty income annotation should be present",
            )
            self.assertEqual(obj.bounty_income, 0)

    def test_annotate_ess_income(self):
        qs = (
            self.journal_entry.division.ledger_corporation_journal.annotate_ess_income()
        )
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "ess_income"),
                "ESS income annotation should be present",
            )
            self.assertEqual(obj.ess_income, 0)

    def test_annotate_miscellaneous(self):
        qs = (
            self.journal_entry.division.ledger_corporation_journal.annotate_miscellaneous()
        )
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "miscellaneous"),
                "Miscellaneous annotation should be present",
            )
            self.assertEqual(obj.miscellaneous, 1000.00)

    def test_annotate_costs(self):
        qs = self.journal_entry.division.ledger_corporation_journal.annotate_costs()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "costs"),
                "Costs annotation should be present",
            )
            self.assertEqual(obj.costs, 0)


class TestCorporationJournalManagerAggregate(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal_entry = CorporationJournalFactory(
            amount=1000,
            date=timezone.datetime.replace(
                timezone.now(),
                year=2016,
                month=10,
                day=29,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
            ref_type="player_donation",
        )

    def test_aggregate_bounty(self):
        result = (
            self.journal_entry.division.ledger_corporation_journal.aggregate_bounty()
        )
        self.assertEqual(result, 0)

    def test_aggregate_costs(self):
        result = (
            self.journal_entry.division.ledger_corporation_journal.aggregate_costs()
        )
        self.assertEqual(result, 0)

    def test_aggregate_miscellaneous(self):
        result = (
            self.journal_entry.division.ledger_corporation_journal.aggregate_miscellaneous()
        )
        self.assertEqual(result, 1000.00)

    def test_aggregate_ref_type(self):
        result = (
            self.journal_entry.division.ledger_corporation_journal.aggregate_ref_type(
                ref_type=["player_donation"], income=True
            )
        )
        self.assertEqual(result, 1000.00)
