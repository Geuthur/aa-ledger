from ninja import NinjaAPI

from django.test import TestCase

from app_utils.testing import create_user_from_evecharacter

from ledger.api.character.ledger import LedgerApiEndpoints
from ledger.tests.test_api._ledgerchardata import CharmonthlyMarch, Charyearly, noData
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all


class ManageApiLedgerCharEndpointsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
                "ledger.char_audit_admin_access",
                "ledger.char_audit_manager",
            ],
        )
        cls.user2, _ = create_user_from_evecharacter(
            1002,
            permissions=[
                "ledger.basic_access",
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

    def test_get_character_ledger_api(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/0/ledger/year/2024/month/3/"

        response = self.client.get(url)
        expected_data = CharmonthlyMarch
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_ledger_api_single(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/1001/ledger/year/2024/month/3/"

        response = self.client.get(url)
        expected_data = CharmonthlyMarch
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_ledger_api_year(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/1001/ledger/year/2024/month/0/"

        response = self.client.get(url)
        print(response.json())
        expected_data = Charyearly
        print(expected_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_ledger_api_no_permission(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/account/1001/ledger/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    def test_get_character_ledger_api_no_data(self):
        self.client.force_login(self.user3)
        url = "/ledger/api/account/0/ledger/year/2024/month/3/"

        response = self.client.get(url)
        expected_data = noData
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)
