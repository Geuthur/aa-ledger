from ninja import NinjaAPI

from django.test import TestCase
from esi.models import Token

from allianceauth.corputils.models import CorpMember, CorpStats
from allianceauth.eveonline.models import EveCorporationInfo
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
                "ledger.advanced_access",
            ],
        )
        cls.user2, _ = create_user_from_evecharacter(
            1002,
        )
        cls.corp = EveCorporationInfo.objects.get(corporation_id=2001)
        cls.token = Token.objects.get(user=cls.user)
        cls.corpstats = CorpStats.objects.create(corp=cls.corp, token=cls.token)
        cls.corpmember = CorpMember.objects.create(
            character_id="1001", character_name="Gneuten", corpstats=cls.corpstats
        )

        cls.api = NinjaAPI()
        cls.manage_api_endpoints = LedgerTemplateApiEndpoints(api=cls.api)

    def test_get_corporation_ledger_template_api_summary_march(self):
        self.client.force_login(self.user)
        url = "/ledger/api/corporation/0/character/0/ledger/template/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "All amounts shown are taxes collected from characters",
            status_code=200,
        )
        self.assertContains(response, "ESS", status_code=200)
        self.assertContains(response, "Summary", status_code=200)

    def test_get_corporation_ledger_template_api_summary_year(self):
        self.client.force_login(self.user)
        url = "/ledger/api/corporation/0/character/0/ledger/template/year/2024/month/0/?corp=true"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "All amounts shown are taxes collected from characters",
            status_code=200,
        )
        self.assertContains(response, "ESS", status_code=200)
        self.assertContains(response, "Summary", status_code=200)
        self.assertContains(response, "2024", status_code=200)

    def test_get_corporation_ledger_template_api_single(self):
        self.client.force_login(self.user)
        url = "/ledger/api/corporation/0/character/1001/ledger/template/year/2024/month/3/"
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "All amounts shown are taxes collected from characters",
            status_code=200,
        )
        self.assertContains(response, "ESS", status_code=200)
        self.assertContains(response, "Gneuten", status_code=200)
        self.assertNotContains(response, "2024", status_code=200)

        # Summary
        self.assertContains(response, "200,000", status_code=200)

    def test_get_corporation_ledger_template_api_single_corp(self):
        self.client.force_login(self.user)
        url = "/ledger/api/corporation/2001/character/2001/ledger/template/year/2024/month/3/?corp=True"
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "All amounts shown are taxes collected from characters",
            status_code=200,
        )
        self.assertContains(response, "ESS", status_code=200)
        self.assertContains(response, "Summary - March", status_code=200)

        # Summary
        self.assertContains(response, "1,400,000", status_code=200)
        self.assertContains(response, "200,000", status_code=200)

    def test_get_corporation_ledger_template_api_year(self):
        self.client.force_login(self.user)
        url = "/ledger/api/corporation/2001/character/1001/ledger/template/year/2024/month/0/"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "200,000", count=2, status_code=200)
        self.assertContains(
            response,
            "All amounts shown are taxes collected from characters",
            status_code=200,
        )
        self.assertContains(response, "ESS", status_code=200)
        self.assertContains(response, "Gneuten", status_code=200)
        self.assertContains(response, "2024", status_code=200)

    def test_get_corporation_template_api_no_permission(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/corporation/1001/character/1001/ledger/template/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
