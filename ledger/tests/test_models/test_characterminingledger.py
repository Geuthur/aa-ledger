# Standard Library
from types import SimpleNamespace
from unittest.mock import patch

# Django
from django.utils import timezone

# Alliance Auth (External Libs)
from eveuniverse.models import EveMarketPrice, EveSolarSystem, EveType

# AA Ledger
from ledger.models.characteraudit import CharacterMiningLedger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import (
    create_miningledger,
    create_owner_from_user,
)

MODULE_PATH = "ledger.models.characteraudit"


class TestCharacterMiningLedgerModel(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(cls.user, owner_type="character")
        cls.eve_type = EveType.objects.get(id=17425)
        cls.eve_system = EveSolarSystem.objects.get(id=30004783)

        cls.eve_type2 = EveType.objects.get(id=16268)
        cls.eve_type_price = EveType.objects.get(id=28437)

        cls.miningentry = create_miningledger(
            character=cls.audit,
            id=1,
            date=timezone.now(),
            type=cls.eve_type,
            system=cls.eve_system,
            quantity=100,
        )
        cls.miningentry2 = create_miningledger(
            character=cls.audit,
            id=2,
            date=timezone.now(),
            type=cls.eve_type2,
            system=cls.eve_system,
            quantity=100,
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
            type_id=1,
            solar_system_id=1,
        )
        cls.eve_market_price = EveMarketPrice.objects.create(
            eve_type=cls.eve_type_price,
            average_price=100,
        )

    def test_str(self):
        """Test string representation of CharacterMiningLedger."""
        self.assertEqual(str(self.miningentry), f"{self.audit} 1")

    def test_create_primary_key(self):
        """Test creation of primary key for CharacterMiningLedger."""
        # Test Data
        primary_key = CharacterMiningLedger.create_primary_key(
            self.audit.eve_character.character_id, self.miningrecord
        )
        # Expected Result
        self.assertEqual(primary_key, "20240101-1-1001-1")

    def test_get_npc_price(self):
        """Test retrieval of NPC price for CharacterMiningLedger."""
        # Test Data
        npc_price = self.miningentry2.get_npc_price()

        # Expected Result
        self.assertIsNotNone(npc_price)
        self.assertEqual(npc_price, 100)

    @patch(MODULE_PATH + ".cache.get", return_value=False)
    @patch(MODULE_PATH + ".EveMarketPrice.objects.update_from_esi")
    def test_update_evemarket_price(self, mock_market_price, mock_cache_get):
        """Test updating Eve market price for CharacterMiningLedger."""
        # Test Data
        mock_market_price.return_value = 1337

        # Test Action
        updated = self.miningentry.update_evemarket_price()

        # Expected Result
        self.assertTrue(mock_market_price.called)
        self.assertEqual(updated, 1337)
