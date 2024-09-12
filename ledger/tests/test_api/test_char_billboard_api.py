from unittest.mock import MagicMock, patch

from ninja import NinjaAPI

from django.test import TestCase
from eveuniverse.models import EveMarketPrice

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from app_utils.testing import add_character_to_user, create_user_from_evecharacter

from ledger.api.character.ledger import LedgerApiEndpoints
from ledger.models.characteraudit import CharacterMiningLedger
from ledger.tests.test_api._billboardchardata import (
    CharmonthlyMarch,
    CharmonthlyMarchMulti,
    CharNoMining,
    Charyearly,
    noData,
)
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
                "ledger.char_audit_admin_manager",
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

    def test_get_character_billbboard_api(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/0/billboard/year/2024/month/3/"

        response = self.client.get(url)

        expected_data = CharmonthlyMarch

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_billbboard_api_multi(self):
        chars = EveCharacter.objects.filter(character_id__in=[1002, 1003])
        for char in chars:
            add_character_to_user(self.user, char)
        self.client.force_login(self.user)
        url = "/ledger/api/account/0/billboard/year/2024/month/3/"

        response = self.client.get(url)

        expected_data = CharmonthlyMarchMulti
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_billbboard_api_cache_no_testing(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/0/billboard/year/2024/month/3/"

        response = self.client.get(url)
        expected_data = CharmonthlyMarch
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_billbboard_api_no_cache_testing(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/0/billboard/year/2024/month/3/"

        response = self.client.get(url)
        expected_data = CharmonthlyMarch
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_billbboard_api_no_cache_no_testing(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/0/billboard/year/2024/month/3/"

        response = self.client.get(url)
        expected_data = CharmonthlyMarch
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_billbboard_api_single(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/1001/billboard/year/2024/month/3/"
        # when
        response = self.client.get(url)
        # then
        expected_data = CharmonthlyMarch
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_billbboard_api_year(self):
        # given
        self.client.force_login(self.user)
        url = "/ledger/api/account/1001/billboard/year/2024/month/0/"
        expected_data = Charyearly
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_billbboard_api_no_permission(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/account/1001/billboard/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    def test_get_character_billbboard_api_no_data(self):
        # given
        self.client.force_login(self.user3)
        url = "/ledger/api/account/0/billboard/year/2024/month/3/"
        # when
        response = self.client.get(url)
        # then
        expected_data = noData
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_billbboard_api_no_mining(self):
        # given
        self.client.force_login(self.user)
        url = "/ledger/api/account/0/billboard/year/2024/month/3/"
        CharacterMiningLedger.objects.all().delete()
        EveMarketPrice.objects.all().delete()
        # when
        response = self.client.get(url)
        # then
        expected_data = CharNoMining
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)
