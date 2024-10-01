from unittest.mock import MagicMock, patch

from ninja import NinjaAPI

from django.test import TestCase

from allianceauth.eveonline.models import EveAllianceInfo
from app_utils.testing import create_user_from_evecharacter

from ledger.api.alliance.ledger import LedgerApiEndpoints
from ledger.tests.test_api._ledgercorpdata import noData
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all


class ManageApiLedgerCorpEndpointsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
                "ledger.advanced_access",
                "ledger.corp_audit_admin_manager",
            ],
        )

        cls.user2, _ = create_user_from_evecharacter(
            1002,
            permissions=[
                "ledger.basic_access",
                "ledger.advanced_access",
            ],
        )

        cls.user3, _ = create_user_from_evecharacter(
            1003,
            permissions=[
                "ledger.basic_access",
            ],
        )

        cls.api = NinjaAPI()
        cls.manage_api_endpoints = LedgerApiEndpoints(api=cls.api)

    def test_get_alliance_ledger_api_single(self):
        self.client.force_login(self.user)
        url = "/ledger/api/alliance/3002/ledger/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_alliance_ledger_api_year_single(self):
        self.client.force_login(self.user)
        url = "/ledger/api/alliance/3001/ledger/year/2024/month/0/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_alliance_ledger_api(self):
        self.client.force_login(self.user)
        url = "/ledger/api/alliance/0/ledger/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_alliance_ledger_api_year(self):
        self.client.force_login(self.user)
        url = "/ledger/api/alliance/0/ledger/year/2024/month/0/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_alliance_ledger_api_no_permission(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/alliance/3001/ledger/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    def test_get_alliance_ledger_api_no_data(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/alliance/0/ledger/year/2000/month/3/"

        response = self.client.get(url)

        expected_data = noData
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_alliance_ledger_api_not_found(self):
        self.client.force_login(self.user3)
        url = "/ledger/api/alliance/3002/ledger/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), "Permission Denied")

    @patch("ledger.models.CorporationWalletJournalEntry.objects.filter")
    def test_get_alliance_ledger_api_single_with_zero_summary_amount(self, mock_filter):
        self.client.force_login(self.user)
        url = "/ledger/api/alliance/3002/ledger/year/2024/month/3/"

        # Mock the queryset to return a journal entry with zero summary amount
        mock_entry = MagicMock()
        mock_entry.get.return_value = 0
        mock_entry.get.side_effect = lambda key, default: (
            0 if key in ["total_bounty", "total_ess"] else default
        )
        mock_filter.return_value.select_related.return_value.annotate_ledger.return_value = [
            mock_entry
        ]

        response = self.client.get(url)

        expected_data = noData
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_alliance_admin(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/alliance/ledger/admin/"
        # when
        response = self.client.get(url)
        # then
        excepted_data = [
            {
                "alliance": {
                    "3002": {"alliance_id": 3002, "alliance_name": "Eulen of War"}
                }
            }
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), excepted_data)

    @patch("ledger.api.alliance.ledger.CorporationAudit.objects.visible_to")
    def test_get_alliance_admin_no_visible(self, mock_visible_to):
        self.client.force_login(self.user2)
        url = "/ledger/api/alliance/ledger/admin/"

        mock_visible_to.return_value = None

        # when
        response = self.client.get(url)
        # then
        self.assertContains(response, "Permission Denied", status_code=403)

    @patch("ledger.api.alliance.ledger.CorporationAudit.objects.visible_to")
    def test_get_alliance_admin_exception(self, mock_visible_to):
        self.client.force_login(self.user)
        url = "/ledger/api/alliance/ledger/admin/"

        corp = EveAllianceInfo.objects.get(alliance_id=3001)

        mock_visible_to.return_value = [corp, "test"]

        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, 200)
