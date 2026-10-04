# Django
from django.utils import timezone

# AA Ledger
from ledger.api.corporation import LedgerEntitySchema
from ledger.api.schema import DateFilter, EntitySchema, LedgerSchema
from ledger.helpers.billboard import BillboardSystem
from ledger.models import CorporationWalletJournalEntry
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CorporationJournalFactory,
    CorporationOwnerFactory,
    DivisionFactory,
)


class TestBillboardSystemCreateBillboards(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CorporationOwnerFactory(user=cls.user)
        cls.division = DivisionFactory(
            corporation=cls.audit,
            division_id=1,
            balance=1000000,
        )
        CorporationJournalFactory(
            division=cls.division,
            amount=1000,
            date=timezone.now().replace(
                year=2016, month=10, day=29, hour=0, minute=0, second=0, microsecond=0
            ),
            ref_type="player_donation",
        )
        cls.ledger_list = [
            LedgerEntitySchema(
                entity=EntitySchema(entity_id=12345, entity_name="Test Entity"),
                ledger=LedgerSchema(
                    bounty=1000, ess=500, miscellaneous=200, costs=300, total=1700
                ),
            )
        ]

    def test_create_billboards_should_return_xy_and_chord_charts(self):
        # Test Data
        filters = DateFilter(year=2016, month=10, day=29)
        journal = CorporationWalletJournalEntry.objects.filter(division=self.division)

        # Test Action
        xy_chart, chord_chart = BillboardSystem().create_billboards(
            filters=filters,
            wallet_journal=journal,
            ledger_list=self.ledger_list,
        )

        # Expected Result
        self.assertIsNotNone(xy_chart)
        self.assertIsNotNone(chord_chart)
        self.assertTrue(xy_chart["series"])
        self.assertTrue(chord_chart["series"])

    def test_create_billboards_should_return_none_without_ledger_data(self):
        # Test Data
        filters = DateFilter(year=2016, month=10, day=29)
        journal = CorporationWalletJournalEntry.objects.filter(division=self.division)

        # Test Action
        xy_chart, chord_chart = BillboardSystem().create_billboards(
            filters=filters,
            wallet_journal=journal,
            ledger_list=[],
        )

        # Expected Result
        self.assertIsNone(xy_chart)
        self.assertIsNone(chord_chart)
