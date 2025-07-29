# Standard Library
from unittest.mock import patch

# Django
from django.test import TestCase

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests.testdata.esi_stub import esi_client_stub
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.managers.general_manager"


class TestGeneralManager(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()

        cls.manager = EveEntity.objects

    @patch("ledger.managers.general_manager.esi")
    def test_get_or_create_esi_existing(self, mock_esi):
        entity = EveEntity.objects.get(eve_id=1001)
        result, created = self.manager.get_or_create_esi(eve_id=1001)
        self.assertEqual(result, entity)
        self.assertFalse(created)

    @patch("ledger.managers.general_manager.esi")
    def test_get_or_create_esi_new(self, mock_esi):
        mock_esi.client = esi_client_stub
        result, created = self.manager.get_or_create_esi(eve_id=9996)
        self.assertEqual(result.eve_id, 9996)
        self.assertEqual(result.name, "Create Character")
        self.assertTrue(created)

    @patch("ledger.managers.general_manager.esi")
    def test_create_bulk_from_esi(self, mock_esi):
        mock_esi.client = esi_client_stub
        result = self.manager.create_bulk_from_esi([9997, 9998])
        self.assertTrue(result)
        self.assertTrue(EveEntity.objects.filter(eve_id=9997).exists())
        self.assertTrue(EveEntity.objects.filter(eve_id=9998).exists())

    @patch("ledger.managers.general_manager.esi")
    def test_update_or_create_esi(self, mock_esi):
        mock_esi.client = esi_client_stub
        result, created = self.manager.update_or_create_esi(eve_id=9999)
        self.assertEqual(result.eve_id, 9999)
        self.assertEqual(result.name, "New Test Character")
        self.assertTrue(created)
