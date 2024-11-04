from unittest.mock import patch

from ninja import NinjaAPI

from django.test import TestCase

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import create_user_from_evecharacter

from ledger.api.character.template import LedgerTemplateApiEndpoints
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all


class ManageApiTemplateCharEndpointsTest(TestCase):
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
                "ledger.char_audit_admin_manager",
            ],
        )
        cls.user2, _ = create_user_from_evecharacter(
            1002,
            permissions=[
                "ledger.basic_access",
            ],
        )

        cls.api = NinjaAPI()
        cls.manage_api_endpoints = LedgerTemplateApiEndpoints(api=cls.api)

    def test_get_character_ledger_template_api(self):
        # given
        self.client.force_login(self.user)
        url = "/ledger/api/account/0/ledger/template/year/2024/month/3/"
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ratting", status_code=200)
        self.assertContains(response, "Mining", status_code=200)
        self.assertContains(response, "200,000", status_code=200)

        self.assertContains(response, "ESS", status_code=200)
        self.assertContains(response, "1,133,333", status_code=200)

        self.assertContains(response, "Donation", status_code=200)

    def test_get_character_ledger_template_api_single(self):
        # given
        self.client.force_login(self.user)
        url = "/ledger/api/account/1001/ledger/template/year/2024/month/3/"
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ratting", status_code=200)
        self.assertContains(response, "Mining", status_code=200)
        self.assertContains(response, "200,000", status_code=200)

        self.assertContains(response, "ESS", status_code=200)
        self.assertContains(response, "1,133,333", status_code=200)

        self.assertContains(response, "Donation", status_code=200)

        # Summary
        self.assertContains(response, "200,000", status_code=200)

    def test_get_character_ledger_template_api_year(self):
        # given
        self.client.force_login(self.user)
        url = "/ledger/api/account/1001/ledger/template/year/2024/month/0/"
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ratting", status_code=200)

        self.assertContains(response, "ESS", status_code=200)
        self.assertContains(response, "1,133,333", status_code=200)

        self.assertContains(response, "Mining", status_code=200)
        self.assertContains(response, "Donation", status_code=200)

        # Summary
        self.assertContains(response, "300,000", count=1, status_code=200)

    def test_get_character_ledger_api_no_permission(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/account/1001/ledger/template/year/2024/month/3/"

        response = self.client.get(url)

        self.assertContains(response, "Permission Denied", status_code=200)

    def test_get_character_ledger_api_not_exist(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/999999/ledger/template/year/2024/month/3/"

        response = self.client.get(url)

        self.assertContains(response, "403 Error", status_code=200)
