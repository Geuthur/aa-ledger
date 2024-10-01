from ninja import NinjaAPI

from django.test import TestCase

from app_utils.testing import create_user_from_evecharacter

from ledger.api.alliance.ledger import LedgerApiEndpoints
from ledger.tests.test_api._billboardcorpdata import noData
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

    def test_get_alliance_billbboard_api_single(self):
        self.client.force_login(self.user)
        url = "/ledger/api/alliance/3002/billboard/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_alliance_billbboard_api_year_3001(self):
        create_user_from_evecharacter(1010)
        create_user_from_evecharacter(1011)
        create_user_from_evecharacter(1012)
        create_user_from_evecharacter(1013)
        create_user_from_evecharacter(1014)
        create_user_from_evecharacter(1015)
        create_user_from_evecharacter(1016)
        create_user_from_evecharacter(1017)
        create_user_from_evecharacter(1018)
        create_user_from_evecharacter(1019)
        create_user_from_evecharacter(1020)
        create_user_from_evecharacter(1021)
        create_user_from_evecharacter(1022)

        self.client.force_login(self.user)
        url = "/ledger/api/alliance/3001/billboard/year/2024/month/0/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_alliance_billbboard_api_year_single(self):
        self.client.force_login(self.user)
        url = "/ledger/api/alliance/3002/billboard/year/2024/month/0/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_alliance_billbboard_api(self):
        self.client.force_login(self.user)
        url = "/ledger/api/alliance/0/billboard/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_alliance_billbboard_api_year(self):
        self.client.force_login(self.user)
        url = "/ledger/api/alliance/0/billboard/year/2024/month/0/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_alliance_billbboard_api_no_permission(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/alliance/3001/billboard/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    def test_get_alliance_billbboard_api_no_data(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/alliance/0/billboard/year/2000/month/3/"

        response = self.client.get(url)

        expected_data = noData
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_alliance_billbboard_api_not_found(self):
        self.client.force_login(self.user3)
        url = "/ledger/api/alliance/3001/billboard/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), "Permission Denied")
