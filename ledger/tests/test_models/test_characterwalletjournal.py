# Django
from django.utils import timezone

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import (
    add_owner_to_user,
    create_wallet_journal_entry,
)

MODULE_PATH = "ledger.models.characteraudit"


class TestCharacterWalletJournalModel(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = add_owner_to_user(
            cls.user, cls.user_character.character.character_id
        )
        cls.eve_character_first_party = EveEntity.objects.get(eve_id=1001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1002)
        cls.journal_entry = create_wallet_journal_entry(
            owner_type="character",
            character=cls.audit,
            entry_id=1,
            amount=1000,
            balance=1000000,
            date=timezone.datetime.replace(
                timezone.now(),
                year=2024,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
            description="Test",
            first_party=cls.eve_character_first_party,
            second_party=cls.eve_character_second_party,
            ref_type="test",
        )

    def test_str(self):
        """Test the string representation of CharacterWalletJournalEntry."""
        self.assertEqual(
            str(self.journal_entry),
            f"Character Wallet Journal: RefType: test - {self.eve_character_first_party.name} -> {self.eve_character_second_party.name}: 1000 ISK",
        )

    def test_get_visible_should_get_list_with_entries(self):
        """Test get_visible method with entries."""
        print(list(self.journal_entry.get_visible(self.user)))
        self.assertEqual(
            list(self.journal_entry.get_visible(self.user)), [self.journal_entry]
        )
