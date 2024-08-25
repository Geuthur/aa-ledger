from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.db.models import Q
from django.test import TestCase

from app_utils.testing import create_user_from_evecharacter

from ledger.managers.corpjournal_manager import CorpWalletManager, CorpWalletManagerBase
from ledger.models import CorporationWalletJournalEntry
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all

MODULE_PATH = "ledger.managers.corpjournal_manager"


class CharManagerQuerySetTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()
        cls.manager = CorpWalletManager()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
            ],
        )

    @patch(MODULE_PATH + ".CorpWalletManagerBase.get_queryset")
    def test_visible_to(self, mock_get_queryset):
        # Setup the mock
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset

        # Create an instance of CorpWalletManagerBase
        manager = CorpWalletManagerBase()

        # Call the visible_to method
        manager.visible_to(self.user)

        # Assertions
        mock_get_queryset.assert_called_once()
        mock_queryset.visible_to.assert_called_once_with(self.user)

    def test_annotate_bounty(self):
        character_ids = [1, 2, 3]

        qs = CorporationWalletJournalEntry.objects.annotate_bounty(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_bounty", qs.query.annotations)

    def test_annotate_ess(self):
        character_ids = [1, 2, 3]

        qs = CorporationWalletJournalEntry.objects.annotate_ess(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_ess", qs.query.annotations)

    def test_annotate_ledger(self):
        result = CorporationWalletJournalEntry.objects.all().annotate_ledger([2001])

        expected_result = [
            {
                "main_character_id": 1001,
                "main_character_name": "Gneuten",
                "alts": [],
                "total_bounty": Decimal("400000.00"),
                "total_ess": Decimal("400000.00"),
            }
        ]

        self.assertEqual(list(result), expected_result)
