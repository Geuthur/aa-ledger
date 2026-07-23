# Standard Library
from types import SimpleNamespace
from unittest.mock import patch

# Django
from django.utils import timezone

# AA Ledger
from ledger.models.characteraudit import CharacterMiningLedger
from ledger.models.general import EveMarketPrice
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CharacterMiningLedgerFactory,
    CharacterOwnerFactory,
)

MODULE_PATH = "ledger.models.characteraudit"


class TestCharacterMiningLedgerModel(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CharacterOwnerFactory(user=cls.user)
        cls.miningentry = CharacterMiningLedgerFactory(
            character=cls.audit,
            date=timezone.now(),
        )
        cls.miningentry2 = CharacterMiningLedgerFactory(
            character=cls.audit,
            date=timezone.now(),
        )
        cls.miningrecord = SimpleNamespace(
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
            type_id=cls.miningentry.type_id,
            solar_system_id=cls.miningentry.system_id,
        )

    def test_str(self):
        """Test string representation of CharacterMiningLedger."""
        self.assertEqual(
            str(self.miningentry),
            f"{self.audit} {self.miningentry.date.strftime('%Y%m%d')}-{self.miningentry.type_id}-{self.audit.eve_id}-{self.miningentry.system_id}",
        )

    def test_create_primary_key(self):
        """Test creation of primary key for CharacterMiningLedger."""
        # Test Data
        primary_key = CharacterMiningLedger.create_primary_key(
            self.audit.eve_character.character_id, self.miningrecord
        )
        # Expected Result
        self.assertEqual(
            primary_key,
            f"20240101-{self.miningrecord.type_id}-{self.audit.eve_character.character_id}-{self.miningrecord.solar_system_id}",
        )

    def test_get_npc_price(self):
        """Test retrieval of NPC price for CharacterMiningLedger."""
        # Test Data
        npc_price = self.miningentry2.get_npc_price()
        eve_market_price = EveMarketPrice.objects.filter(
            eve_type=self.miningentry2.type
        ).first()

        # Expected Result
        self.assertIsNotNone(npc_price)
        self.assertEqual(npc_price, eve_market_price.average_price)

    @patch(MODULE_PATH + ".EveMarketPrice.objects.update_from_esi")
    def test_update_evemarket_price(self, mock_market_price):
        """Test updating Eve market price for CharacterMiningLedger."""
        # Test Data
        mock_market_price.return_value = 1337

        # Test Action
        updated = self.miningentry.update_evemarket_price()

        # Expected Result
        self.assertTrue(mock_market_price.called)
        self.assertEqual(updated, 1337)
