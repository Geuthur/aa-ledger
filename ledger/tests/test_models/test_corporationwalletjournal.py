# Alliance Auth (External Libs)
from evesde_factory.utils import add_permission_to_user

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CorporationJournalFactory,
    CorporationOwnerFactory,
    DivisionFactory,
)

MODULE_PATH = "ledger.models.corporationaudit"


class TestCorporationWalletJournalModel(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = CorporationOwnerFactory(user=cls.user)
        cls.division = DivisionFactory(
            corporation=cls.owner, name="MEGA KONTO", balance=1000000, division_id=1
        )
        cls.journal_entry = CorporationJournalFactory(
            division=cls.division,
            amount=1000,
            ref_type="player_donation",
        )

    def test_str(self):
        """Test the string representation of CorporationWalletJournalEntry."""
        self.assertEqual(
            str(self.journal_entry),
            f"Corporation Wallet Journal: RefType: player_donation - {self.journal_entry.first_party.name} -> {self.journal_entry.second_party.name}: 1000 ISK",
        )

    def test_get_visible_with_permission(self):
        """
        Test get_visible method with permissions.

        ### Expected Result
        - User with permissions can access journal entries.
        """
        # Test Data
        self.user = add_permission_to_user(
            user=self.user, permissions=["ledger.advanced_access"]
        )

        # Expected Result
        self.assertEqual(
            list(self.journal_entry.get_visible(self.user)), [self.journal_entry]
        )

    def test_get_visible_without_permission(self):
        """
        Test get_visible method without permissions.

        ### Expected Result
        - User without permissions cannot access any journal entries.
        """
        self.assertEqual(list(self.journal_entry.get_visible(self.user)), [])
