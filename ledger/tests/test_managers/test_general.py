from unittest.mock import patch

from django.test import TestCase

from allianceauth.eveonline.providers import ObjectNotFound

from ledger.models.general import EveEntity
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_eveentity

MODULE_PATH = "ledger.managers.general_manager"


class GeneralQuerySetTest(TestCase):
    @classmethod
    def setUpclass(cls) -> None:
        super().setUpClass()
        load_allianceauth()

    def test_get_or_create_esi(self):
        load_eveentity()
        # given/when
        result = EveEntity.objects.get_or_create_esi(eve_id=1001)
        # then
        self.assertEqual(result[0].eve_id, 1001)

    @patch(MODULE_PATH + ".EveEntityManager.update_or_create_esi")
    def test_get_or_create_esi_doesnotexist(self, mock_update_or_create_esi):
        # given
        mock_update_or_create_esi.return_value = (EveEntity(eve_id=1001), True)
        # when
        result = EveEntity.objects.get_or_create_esi(eve_id=1001)
        # then
        self.assertEqual(result[0].eve_id, 1001)

    @patch(MODULE_PATH + ".esi")
    def test_update_or_create_esi(self, mock_esi):
        # given
        mock_esi.client.Universe.post_universe_names.return_value.results.return_value = [
            {
                "id": 1001,
                "name": "Gneuten",
                "category": "character",
            }
        ]
        # when
        result, _ = EveEntity.objects.update_or_create_esi(eve_id=1001)
        expected_result = EveEntity.objects.get(eve_id=1001)
        # then
        self.assertEqual(result, expected_result)

    @patch(MODULE_PATH + ".esi")
    def test_update_or_create_esi_unknown(self, mock_esi):
        # given
        mock_esi.client.Universe.post_universe_names.return_value.results.return_value = (
            []
        )
        # when
        with self.assertRaises(ObjectNotFound):
            EveEntity.objects.update_or_create_esi(eve_id=1001)

    @patch(MODULE_PATH + ".esi")
    @patch("ledger.models.general.EveEntity.objects.bulk_create")
    def test_create_bulk_from_esi(self, mock_bulk_create, mock_esi):
        # given
        mock_esi.client.Universe.post_universe_names.return_value.results.return_value = [
            {
                "id": 1001,
                "name": "Gneuten",
                "category": "character",
            },
            {
                "id": 1002,
                "name": "rotze Rotineque",
                "category": "character",
            },
        ]
        # when
        result = EveEntity.objects.create_bulk_from_esi([1001, 1002])
        # then
        self.assertTrue(result)
        mock_bulk_create.assert_called_once()

    def test_create_bulk_from_esi_no_ids(self):
        # given
        # when
        result = EveEntity.objects.create_bulk_from_esi([])
        # then
        self.assertTrue(result)
