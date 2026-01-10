# Django
from django.utils import timezone

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import (
    add_new_permission_to_user,
    create_division,
    create_owner_from_user,
    create_wallet_journal_entry,
)

MODULE_PATH = "ledger.models.corporationaudit"


class TestCorporationWalletJournalModel(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = create_owner_from_user(cls.user, owner_type="corporation")
        cls.division = create_division(
            corporation=cls.owner, name="MEGA KONTO", balance=1000000, division_id=1
        )

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=1001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1002)

        cls.journal_entry = create_wallet_journal_entry(
            owner_type="corporation",
            division=cls.division,
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
        """Test the string representation of CorporationWalletJournalEntry."""
        self.assertEqual(
            str(self.journal_entry),
            f"Corporation Wallet Journal: RefType: test - {self.eve_character_first_party.name} -> {self.eve_character_second_party.name}: 1000 ISK",
        )

    def test_get_visible_with_permission(self):
        """
        Test get_visible method with permissions.

        ### Expected Result
        - User with permissions can access journal entries.
        """
        # Test Data
        self.user = add_new_permission_to_user(
            user=self.user, permission_name="ledger.advanced_access"
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
