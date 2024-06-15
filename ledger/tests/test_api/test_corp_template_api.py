from ninja import NinjaAPI

from django.test import TestCase

from app_utils.testing import create_user_from_evecharacter

from ledger.api.corporation.template import LedgerTemplateApiEndpoints
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all


class ManageApiTemplateCorpEndpointsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
                "ledger.corp_audit_admin_access",
                "ledger.corp_audit_manager",
            ],
        )
        cls.user2, _ = create_user_from_evecharacter(
            1002,
        )

        cls.api = NinjaAPI()
        cls.manage_api_endpoints = LedgerTemplateApiEndpoints(api=cls.api)

    def test_get_corporation_ledger_template_api(self):
        self.client.force_login(self.user)
        url = "/ledger/api/corporation/0/ledger/template/year/2024/month/3/"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "200,000", count=2, status_code=200)
        self.assertContains(response, "Ratting", status_code=200)
        self.assertContains(response, "ESS", status_code=200)

    def test_get_corporation_ledger_template_api_single(self):
        self.client.force_login(self.user)
        url = "/ledger/api/corporation/1001/ledger/template/year/2024/month/3/"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "200,000", count=2, status_code=200)
        self.assertContains(response, "Ratting", status_code=200)
        self.assertContains(response, "ESS", status_code=200)

    def test_get_corporation_template_api_no_permission(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/corporation/1001/ledger/template/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
