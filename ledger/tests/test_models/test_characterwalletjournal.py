# Django
from django.utils import timezone

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import CharacterJournalFactory, CharacterOwnerFactory

MODULE_PATH = "ledger.models.characteraudit"


class TestCharacterWalletJournalModel(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CharacterOwnerFactory(user=cls.user)
        cls.journal_entry = CharacterJournalFactory(
            character=cls.audit,
            amount=1000,
            ref_type="player_donation",
        )

    def test_str(self):
        """Test the string representation of CharacterWalletJournalEntry."""
        self.assertEqual(
            str(self.journal_entry),
            f"Character Wallet Journal: RefType: player_donation - {self.journal_entry.first_party.name} -> {self.journal_entry.second_party.name}: 1000 ISK",
        )

    def test_get_visible_should_get_list_with_entries(self):
        """Test get_visible method with entries."""
        self.assertEqual(
            list(self.journal_entry.get_visible(self.user)), [self.journal_entry]
        )
