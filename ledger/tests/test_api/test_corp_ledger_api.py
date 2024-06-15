from ninja import NinjaAPI

from django.test import TestCase

from app_utils.testing import create_user_from_evecharacter

from ledger.api.corporation.ledger import LedgerApiEndpoints
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
                "ledger.corp_audit_admin_access",
                "ledger.corp_audit_manager",
            ],
        )
        cls.user2, _ = create_user_from_evecharacter(
            1002,
        )

        cls.api = NinjaAPI()
        cls.manage_api_endpoints = LedgerApiEndpoints(api=cls.api)

    def test_get_corporation_ledger_api(self):
        self.client.force_login(self.user)
        url = "/ledger/api/corporation/0/ledger/year/2024/month/3/"

        response = self.client.get(url)
        expected_data = [
            {
                "ratting": [
                    {
                        "main_id": 1001,
                        "main_name": "Gneuten",
                        "alt_names": [],
                        "total_amount": "200000.00",
                        "total_amount_ess": "200000.00",
                    }
                ],
                "total": {
                    "total_amount": "200000.00",
                    "total_amount_ess": "200000.00",
                    "total_amount_all": "400000.00",
                    "total_amount_mining": 0,
                    "total_amount_others": 0,
                },
                "billboard": {
                    "walletcharts": [],
                    "charts": [
                        ["Gneuten", "100"],
                    ],
                    "rattingbar": [
                        [
                            "x",
                            "2024-06-01",
                            "2024-06-02",
                            "2024-06-03",
                            "2024-06-04",
                            "2024-06-05",
                            "2024-06-06",
                            "2024-06-07",
                            "2024-06-08",
                            "2024-06-09",
                            "2024-06-10",
                            "2024-06-11",
                            "2024-06-12",
                            "2024-06-13",
                            "2024-06-14",
                            "2024-06-15",
                            "2024-06-16",
                            "2024-06-17",
                            "2024-06-18",
                            "2024-06-19",
                            "2024-06-20",
                            "2024-06-21",
                            "2024-06-22",
                            "2024-06-23",
                            "2024-06-24",
                            "2024-06-25",
                            "2024-06-26",
                            "2024-06-27",
                            "2024-06-28",
                            "2024-06-29",
                            "2024-06-30",
                        ],
                        [
                            "Ratting",
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            200000,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                        ],
                        [
                            "ESS Payout",
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            200000,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                        ],
                        ["Miscellaneous"],
                        ["Mining"],
                    ],
                    "workflowgauge": [],
                },
            }
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_corporation_ledger_api_single(self):
        self.client.force_login(self.user)
        url = "/ledger/api/corporation/2001/ledger/year/2024/month/3/"

        response = self.client.get(url)
        expected_data = [
            {
                "ratting": [
                    {
                        "main_id": 1001,
                        "main_name": "Gneuten",
                        "alt_names": [],
                        "total_amount": "200000.00",
                        "total_amount_ess": "200000.00",
                    }
                ],
                "total": {
                    "total_amount": "200000.00",
                    "total_amount_ess": "200000.00",
                    "total_amount_all": "400000.00",
                    "total_amount_mining": 0,
                    "total_amount_others": 0,
                },
                "billboard": {
                    "walletcharts": [],
                    "charts": [
                        ["Gneuten", "100"],
                    ],
                    "rattingbar": [
                        [
                            "x",
                            "2024-06-01",
                            "2024-06-02",
                            "2024-06-03",
                            "2024-06-04",
                            "2024-06-05",
                            "2024-06-06",
                            "2024-06-07",
                            "2024-06-08",
                            "2024-06-09",
                            "2024-06-10",
                            "2024-06-11",
                            "2024-06-12",
                            "2024-06-13",
                            "2024-06-14",
                            "2024-06-15",
                            "2024-06-16",
                            "2024-06-17",
                            "2024-06-18",
                            "2024-06-19",
                            "2024-06-20",
                            "2024-06-21",
                            "2024-06-22",
                            "2024-06-23",
                            "2024-06-24",
                            "2024-06-25",
                            "2024-06-26",
                            "2024-06-27",
                            "2024-06-28",
                            "2024-06-29",
                            "2024-06-30",
                        ],
                        [
                            "Ratting",
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            200000,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                        ],
                        [
                            "ESS Payout",
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            200000,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                        ],
                        ["Miscellaneous"],
                        ["Mining"],
                    ],
                    "workflowgauge": [],
                },
            }
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_corporation_ledger_api_no_permission(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/corporation/2001/ledger/year/2024/month/3/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
