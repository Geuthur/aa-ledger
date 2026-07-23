# Standard Library
from http import HTTPStatus
from unittest.mock import MagicMock, patch

# Third Party
import pook

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CharacterOwnerFactory,
    ItemTypeFactory,
    SolarSystemFactory,
)

MODULE_PATH = "ledger.managers.character_mining_manager"
CHARACTEROWNER_PATH = "ledger.models.characteraudit.CharacterMiningLedger"


@patch(CHARACTEROWNER_PATH + ".update_evemarket_price")
class TestCharacterMiningManager(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CharacterOwnerFactory(user=cls.user)
        cls.token = cls.user.token_set.first()
        cls.audit.get_token = MagicMock(return_value=cls.token)

    @pook.on
    def test_update_mining_ledger(self, _):
        """
        Test updating the character mining ledger.

        This test verifies that the mining ledger entries are correctly updated
        from ESI data. It checks that the entries have the expected quantity, system_id,
        and type_id.

        ### Expected Result
        - Mining ledger entries are updated correctly.
        - Entries have correct quantity, system_id, and type_id.
        """
        # Test Data
        ItemTypeFactory(id=17425, name="Tritanium")
        SolarSystemFactory(id=30004783, name="Jita")
        pook.get(
            f"https://esi.evetech.net/characters/{self.user_character.character_id}/mining",
            reply=HTTPStatus.OK,
            response_json=[
                {
                    "date": "2014-10-29",
                    "quantity": 5000,
                    "type_id": 17425,
                    "solar_system_id": 30004783,
                }
            ],
        )

        # Test Action
        self.audit.update_mining_ledger(force_refresh=False)

        # Excepted Results
        obj = self.audit.ledger_character_mining.filter(
            date__contains="2014-10-29"
        ).first()
        self.assertEqual(obj.quantity, 5000)
        self.assertEqual(obj.system_id, 30004783)
        self.assertEqual(obj.type_id, 17425)
