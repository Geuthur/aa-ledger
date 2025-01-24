from datetime import datetime
from unittest.mock import MagicMock, patch

from ninja import NinjaAPI

from django.test import TestCase
from django.utils import timezone
from eveuniverse.models import EveMarketPrice

from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from app_utils.testing import add_character_to_user, create_user_from_evecharacter

from ledger.api.api_helper.character_helper import CharacterProcess
from ledger.api.ledger import LedgerApiEndpoints
from ledger.models.characteraudit import CharacterMiningLedger
from ledger.models.events import Events
from ledger.tests.test_api import _ledgercorpdata
from ledger.tests.test_api._ledgerchardata import (
    CharmonthlyMarch,
    CharmonthlyMarchMulti,
    CharmonthlyMarchWithTaxEvent,
    CharNoMining,
    Charyearly,
    noData,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all

MODULE_PATH = "ledger.api.api_helper.character_helper"


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
                "ledger.advanced_access",
                "ledger.char_audit_admin_manager",
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
        cls.user_with_no_permission, _ = create_user_from_evecharacter(
            1003,
            permissions=[
                "ledger.basic_access",
            ],
        )

        cls.user_with_no_data, _ = create_user_from_evecharacter(
            1022,
            permissions=[
                "ledger.basic_access",
                "ledger.advanced_access",
            ],
        )

        cls.api = NinjaAPI()
        cls.manage_api_endpoints = LedgerApiEndpoints(api=cls.api)

    @patch(MODULE_PATH + ".get_alts_queryset")
    def test_get_alts_with_exception(self, mock_get_alts_queryset):
        process = CharacterProcess(chars=[], year=2024, month=3)
        main = [1]
        mock_get_alts_queryset.side_effect = Exception("Test exception")
        result = process.get_alts(main)
        self.assertIsNone(result)
        mock_get_alts_queryset.assert_called_once_with(1)

    def test_get_ledger_api_with_tax_event(self):
        Events.objects.create(
            title="Test Event",
            date_start=datetime(2024, 3, 19, 0, 0, 0, tzinfo=timezone.utc),
            date_end=datetime(2024, 3, 19, 23, 59, 59, tzinfo=timezone.utc),
            description="This is a test event.",
            char_ledger=True,
            location="Test Location",
        )

        self.client.force_login(self.user)
        url = "/ledger/api/character/0/ledger/year/2024/month/3/"

        response = self.client.get(url)

        expected_data = CharmonthlyMarchWithTaxEvent
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

        # Corporation
        url = "/ledger/api/corporation/0/ledger/year/2024/month/3/"

        response = self.client.get(url)
        expected_data = _ledgercorpdata.CorpdatamanyWithTaxEvent

        Events.objects.all().delete()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_ledger_api(self):
        self.client.force_login(self.user)
        url = "/ledger/api/character/0/ledger/year/2024/month/3/"

        response = self.client.get(url)

        expected_data = CharmonthlyMarch
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

        # Corporation
        url = "/ledger/api/corporation/0/ledger/year/2024/month/3/"

        response = self.client.get(url)
        expected_data = _ledgercorpdata.Corpdatamany
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

        # Alliance
        url = "/ledger/api/alliance/0/ledger/year/2024/month/3/"

        response = self.client.get(url)
        expected_data = _ledgercorpdata.Corpdatamany
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

        # Wrong Type
        url = "/ledger/api/test/0/ledger/year/2024/month/3/"

        response = self.client.get(url)
        self.assertContains(response, "No Entity Type found", status_code=403)

    def test_get_ledger_api_multi(self):
        chars = EveCharacter.objects.filter(character_id__in=[1002, 1003])
        for char in chars:
            add_character_to_user(self.user, char)
        self.client.force_login(self.user)
        url = "/ledger/api/character/0/ledger/year/2024/month/3/"

        response = self.client.get(url)

        expected_data = CharmonthlyMarchMulti
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_ledger_api_single(self):
        self.client.force_login(self.user)
        url = "/ledger/api/character/1001/ledger/year/2024/month/3/"
        # when
        response = self.client.get(url)
        # then
        expected_data = CharmonthlyMarch
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

        # Corporation
        url = "/ledger/api/corporation/2001/ledger/year/2024/month/3/"

        response = self.client.get(url)
        expected_data = _ledgercorpdata.Corpdatamany
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

        # Alliance
        url = "/ledger/api/alliance/3001/ledger/year/2024/month/3/"

        response = self.client.get(url)

        expected_data = _ledgercorpdata.Corpdatamany
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_ledger_api_year(self):
        # given
        self.client.force_login(self.user)
        url = "/ledger/api/character/1001/ledger/year/2024/month/0/"
        expected_data = Charyearly
        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

        # Corporation
        url = "/ledger/api/corporation/2001/ledger/year/2024/month/0/"

        response = self.client.get(url)

        expected_data = _ledgercorpdata.Corpdatamany
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

        # Alliance
        url = "/ledger/api/alliance/3001/ledger/year/2024/month/0/"

        response = self.client.get(url)

        expected_data = _ledgercorpdata.Corpdatamany
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_ledger_api_no_permission(self):
        self.client.force_login(self.user_with_no_permission)
        url = "/ledger/api/character/1001/ledger/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

        url = "/ledger/api/corporation/2001/ledger/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

        url = "/ledger/api/alliance/3001/ledger/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    def test_get_ledger_api_no_data(self):
        # given
        self.client.force_login(self.user_with_no_data)
        url = "/ledger/api/character/0/ledger/year/2024/month/3/"
        # when
        response = self.client.get(url)
        # then
        expected_data = noData
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

        self.client.force_login(self.user)
        # Corporation
        url = "/ledger/api/corporation/0/ledger/year/2024/month/12/"
        # when
        response = self.client.get(url)
        # then
        expected_data = _ledgercorpdata.noData
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

        # Alliance
        url = "/ledger/api/alliance/0/ledger/year/2024/month/12/"
        # when
        response = self.client.get(url)
        # then
        expected_data = _ledgercorpdata.noData
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_ledger_api_amount_is_zero(self):
        # given
        self.client.force_login(self.user_with_no_data)
        url = "/ledger/api/character/0/ledger/year/2024/month/3/"
        # when
        response = self.client.get(url)
        # then
        expected_data = noData
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_character_ledger_api_no_mining(self):
        # given
        self.client.force_login(self.user)
        url = "/ledger/api/character/0/ledger/year/2024/month/3/"
        CharacterMiningLedger.objects.all().delete()
        EveMarketPrice.objects.all().delete()
        # when
        response = self.client.get(url)
        # then
        expected_data = CharNoMining
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    @patch("ledger.models.CorporationWalletJournalEntry.objects.filter")
    def test_get_corporation_ledger_api_single_with_zero_summary_amount(
        self, mock_filter
    ):
        self.client.force_login(self.user)
        url = "/ledger/api/corporation/2002/ledger/year/2024/month/3/"

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

        expected_data = _ledgercorpdata.noData
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    @patch("ledger.api.ledger.admin.CharacterAudit.objects.visible_eve_characters")
    def test_get_admin_no_visible(self, mock_visible_to):
        self.client.force_login(self.user_with_no_permission)
        url = "/ledger/api/character/ledger/admin/"

        mock_visible_to.return_value = None

        # when
        response = self.client.get(url)
        # then
        self.assertContains(response, "Permission Denied", status_code=403)

    @patch("ledger.api.ledger.admin.CorporationAudit.objects.visible_to")
    def test_get_corporation_admin_no_visible(self, mock_visible_to):
        self.client.force_login(self.user2)
        # Corporation
        url = "/ledger/api/corporation/ledger/admin/"

        mock_visible_to.return_value = None

        response = self.client.get(url)
        # then
        self.assertContains(response, "Permission Denied", status_code=403)

        # Alliance
        url = "/ledger/api/alliance/ledger/admin/"
        # when
        response = self.client.get(url)
        # then
        self.assertContains(response, "Permission Denied", status_code=403)

    def test_get_admin(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/character/ledger/admin/"

        # when
        response = self.client.get(url)
        # then
        excepted_data = [
            {
                "character": {
                    "1002": {
                        "character_id": 1002,
                        "character_name": "rotze Rotineque",
                        "corporation_id": 2002,
                        "corporation_name": "Eulenclub",
                    }
                }
            }
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), excepted_data)

        # Corporation
        url = "/ledger/api/corporation/ledger/admin/"
        # when
        response = self.client.get(url)
        # then
        excepted_data = [
            {
                "corporation": {
                    "2002": {"corporation_id": 2002, "corporation_name": "Eulenclub"}
                }
            }
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), excepted_data)

        # Alliance
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

    @patch("ledger.api.ledger.admin.UserProfile.objects.filter")
    def test_get_character_admin_attribute_error(self, mock_user_profile_filter):
        # given
        self.client.force_login(self.user)
        url = "/ledger/api/character/ledger/admin/"

        # Mock the UserProfile to return a character with missing attributes
        mock_user_profile_filter.return_value = [MagicMock(main_character="LUL")]

        # when
        response = self.client.get(url)

        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"character": {}}])

    @patch("ledger.api.ledger.admin.CorporationAudit.objects.visible_to")
    def test_get_admin_exception(self, mock_visible_to):
        self.client.force_login(self.user)
        # Corporation
        url = "/ledger/api/corporation/ledger/admin/"

        corp = EveCorporationInfo.objects.get(corporation_id=2001)

        mock_visible_to.return_value = [corp, "test"]

        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, 200)

        # Alliance
        url = "/ledger/api/alliance/ledger/admin/"

        corp = EveAllianceInfo.objects.get(alliance_id=3001)

        mock_visible_to.return_value = [corp, "test"]

        # when
        response = self.client.get(url)
        # then
        self.assertEqual(response.status_code, 200)
