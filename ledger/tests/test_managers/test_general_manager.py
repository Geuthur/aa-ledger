# Standard Library
from unittest.mock import patch

# AA Ledger
from ledger.models.general import EveEntity, EveMarketPrice
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.esi_stub_openapi import EsiEndpoint, create_esi_client_stub

MODULE_PATH = "ledger.managers.general_manager"

LEDGER_EVE_ENTITY_ENDPOINTS = [
    EsiEndpoint("Universe", "PostUniverseNames", "ids"),
    EsiEndpoint("Universe", "GetUniverseNames", "ids"),
    EsiEndpoint("Market", "GetMarketsPrices", ()),
]


class TestGeneralManager(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = EveEntity.objects

    @patch("ledger.managers.general_manager.esi")
    def test_get_or_create_esi_existing(self, mock_esi):
        """
        Test retrieving an existing EveEntity from the database.

        This test verifies that an existing EveEntity is correctly retrieved
        from the database without making an ESI API call. It checks that the
        entity has the expected eve_id and that the created flag is set to False.

        ### Expected Result
        - EveEntity is retrieved correctly.
        - Entity has correct eve_id.
        - Created flag is False.
        """
        # Test Data
        entity = EveEntity.objects.get(eve_id=1001)

        # Test Action
        result, created = self.manager.get_or_create_esi(eve_id=1001)

        # Expected Results
        self.assertEqual(result, entity)
        self.assertFalse(created)

    @patch("ledger.managers.general_manager.esi")
    def test_get_or_create_esi_new(self, mock_esi):
        """
        Test creating a new EveEntity from ESI data.

        This test verifies that a new EveEntity is correctly created
        based on data fetched from the ESI API. It checks that the entity has the
        expected eve_id and name, and that the created flag is set to True.

        ### Expected Result
        - EveEntity is created correctly.
        - Entity has correct eve_id and name.
        - Created flag is True.
        """
        # Test Data
        mock_esi.client = create_esi_client_stub(endpoints=LEDGER_EVE_ENTITY_ENDPOINTS)

        # Test Action
        result, created = self.manager.get_or_create_esi(eve_id=9996)

        # Expected Results
        self.assertEqual(result.eve_id, 9996)
        self.assertEqual(result.name, "Create Character")
        self.assertTrue(created)

    @patch("ledger.managers.general_manager.esi")
    def test_create_bulk_from_esi(self, mock_esi):
        """
        Test bulk creation of EveEntity objects from ESI data.

        This test verifies that multiple EveEntity objects are correctly created
        based on data fetched from the ESI API. It checks that the entities with
        the specified eve_ids exist in the database after the operation.

        ### Expected Result
        - Multiple EveEntity objects are created correctly.
        - Entities with specified eve_ids exist in the database.
        """
        # Test Data
        mock_esi.client = create_esi_client_stub(endpoints=LEDGER_EVE_ENTITY_ENDPOINTS)

        # Test Action
        result = self.manager.create_bulk_from_esi([9997, 9998])

        # Expected Results
        self.assertTrue(result)
        self.assertTrue(EveEntity.objects.filter(eve_id=9997).exists())
        self.assertTrue(EveEntity.objects.filter(eve_id=9998).exists())

    @patch("ledger.managers.general_manager.esi")
    def test_update_or_create_esi(self, mock_esi):
        """
        Test updating or creating an EveEntity from ESI data.

        This test verifies that the EveEntity is correctly updated or created
        based on data fetched from the ESI API. It checks that the entity has the
        expected eve_id and name, and that the created flag is set to True.

        ### Expected Result
        - EveEntity is updated or created correctly.
        - Entity has correct eve_id and name.
        - Created flag is True.
        """
        # Test Data
        mock_esi.client = create_esi_client_stub(endpoints=LEDGER_EVE_ENTITY_ENDPOINTS)

        # Test Action
        result, created = self.manager.update_or_create_esi(eve_id=9999)

        # Expected Results
        self.assertEqual(result.eve_id, 9999)
        self.assertEqual(result.name, "New Test Character")
        self.assertTrue(created)

    @patch("ledger.managers.general_manager.esi")
    def test_update_or_create_esi_market_price(self, mock_esi):
        """
        Test updating or creating EveMarketPrice from ESI data.

        This test verifies that the EveMarketPrice is correctly updated or created
        based on data fetched from the ESI API. It checks that the market price has the
        expected eve_type_id and average_price, and that the created flag is set to True.

        ### Expected Result
        - EveMarketPrice is updated or created correctly.
        - Market price has correct eve_type_id and average_price.
        - Created flag is True.
        """
        # Test Data
        mock_esi.client = create_esi_client_stub(endpoints=LEDGER_EVE_ENTITY_ENDPOINTS)

        # Test Action
        result = EveMarketPrice.objects.update_from_esi()

        # Expected Results
        self.assertEqual(result, 1)
        self.assertTrue(
            EveMarketPrice.objects.filter(
                eve_type_id=17425, average_price=100.0
            ).exists()
        )
