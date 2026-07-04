# Standard Library
from unittest.mock import MagicMock

# Django
from django.utils import timezone

# AA Ledger
from ledger.api.corporation import LedgerEntitySchema
from ledger.api.schema import CorporationLedgerRequestInfo, EntitySchema, LedgerSchema
from ledger.models import (
    CorporationBillboardEntry,
    CorporationWalletJournalEntry,
    EveEntity,
)
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import (
    create_division,
    create_owner_from_user,
    create_wallet_journal_entry,
)

MODULE_PATH = "ledger.managers.ledger_manager"


class TestBillboardEntryManager(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(user=cls.user, owner_type="corporation")
        cls.eve_character_first_party = EveEntity.objects.get(eve_id=1001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1002)

        cls.division = create_division(
            corporation=cls.audit,
            division_id=1,
            balance=1000000,
        )

        cls.journal_entry = create_wallet_journal_entry(
            owner_type="corporation",
            division=cls.division,
            context_id=1,
            entry_id=1,
            amount=1000,
            balance=2000,
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
            description="Test Journal",
            first_party=cls.eve_character_first_party,
            second_party=cls.eve_character_second_party,
            ref_type="player_donation",
        )
        cls.token = cls.user_character.user.token_set.first()
        cls.audit.get_token = MagicMock(return_value=cls.token)

    def test_update_or_create_billboard_entry(self):
        """
        Test the update_or_create_billboard_entry method of the BillboardEntryManager.

        This test verifies that the method correctly updates or creates a billboard entry
        based on the provided owner, request information, wallet journal, ledger list, and mining journal.

        ### Results:
        - The billboard entry is updated or created successfully.
        - The method handles both character and corporation owners correctly.
        """
        # Test Data
        request_info = CorporationLedgerRequestInfo(
            owner_id=self.audit.eve_id,
            year=2024,
            month=6,
            day=30,
        )
        ledger_data = LedgerSchema(
            bounty=1000,
            ess=500,
            miscellaneous=200,
            costs=300,
            total=1700,
        )
        entity = EntitySchema(
            entity_id=12345,
            entity_name="Test Entity",
        )

        ledger_list = []
        ledger_list.append(
            LedgerEntitySchema(
                entity=entity,
                ledger=ledger_data,
            )
        )
        journal = CorporationWalletJournalEntry.objects.filter(division=self.division)

        CorporationBillboardEntry.objects.update_or_create_billboard_entry(
            owner=self.audit,
            request_info=request_info,
            wallet_journal=journal,
            ledger_list=ledger_list,
        )

        # Expected Result
        billboard_entry = CorporationBillboardEntry.objects.filter(
            owner=self.audit,
            year=2024,
            month=6,
            day=30,
        ).first()
        self.assertIsNotNone(billboard_entry)
        self.assertEqual(billboard_entry.owner, self.audit)
        self.assertEqual(billboard_entry.year, 2024)
        self.assertEqual(billboard_entry.month, 6)
        self.assertEqual(billboard_entry.day, 30)
        self.assertIsNotNone(billboard_entry.xy_billboard)
        self.assertIsNotNone(billboard_entry.chord_billboard)
