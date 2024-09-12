from typing import Optional

from ninja import NinjaAPI

from django.test import TestCase

from app_utils.testing import create_user_from_evecharacter

from ledger.api.corporation.journal import LedgerJournalApiEndpoints
from ledger.models.corporationaudit import CorporationWalletJournalEntry
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all


class ManageApiJournalCorpEndpointsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()

        cls.user, _ = create_user_from_evecharacter(
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

        cls.api = NinjaAPI()
        cls.manage_api_endpoints = LedgerJournalApiEndpoints(api=cls.api)

    def test_get_corporation_journal_api_single(self):
        self.client.force_login(self.user)
        url = "/ledger/api/corporation/2001/wallet/"

        wallet_journal = (
            CorporationWalletJournalEntry.get_visible(self.user)
            .filter(division__corporation__corporation__corporation_id=2001)
            .select_related("first_party", "second_party", "division")
            .order_by("-entry_id")
        )

        start_count = (1 - 1) * 10000
        end_count = 1 * 10000

        wallet_journal = wallet_journal[start_count:end_count]

        response = self.client.get(url)

        expected_data = []
        for journal in wallet_journal:
            expected_data.append(
                {
                    "division": f"{journal.division.division} {journal.division.name}",
                    "id": journal.entry_id,
                    "date": journal.date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "first_party": {
                        "id": journal.first_party.eve_id,
                        "name": journal.first_party.name,
                        "cat": journal.first_party.category,
                    },
                    "second_party": {
                        "id": journal.second_party.eve_id,
                        "name": journal.second_party.name,
                        "cat": journal.second_party.category,
                    },
                    "ref_type": journal.ref_type,
                    "balance": float(journal.balance),
                    "amount": float(journal.amount),
                    "reason": journal.reason,
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_corporation_journal_api_single_ref_types(self):
        self.client.force_login(self.user)
        url = "/ledger/api/corporation/2001/wallet/?type_refs=bounty_prizes,ess_escrow_transfer"

        wallet_journal = (
            CorporationWalletJournalEntry.get_visible(self.user)
            .filter(division__corporation__corporation__corporation_id=2001)
            .select_related("first_party", "second_party", "division")
            .order_by("-entry_id")
        )

        start_count = (1 - 1) * 10000
        end_count = 1 * 10000

        wallet_journal = wallet_journal[start_count:end_count]

        response = self.client.get(url)

        expected_data = []
        for journal in wallet_journal:
            expected_data.append(
                {
                    "division": f"{journal.division.division} {journal.division.name}",
                    "id": journal.entry_id,
                    "date": journal.date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "first_party": {
                        "id": journal.first_party.eve_id,
                        "name": journal.first_party.name,
                        "cat": journal.first_party.category,
                    },
                    "second_party": {
                        "id": journal.second_party.eve_id,
                        "name": journal.second_party.name,
                        "cat": journal.second_party.category,
                    },
                    "ref_type": journal.ref_type,
                    "balance": float(journal.balance),
                    "amount": float(journal.amount),
                    "reason": journal.reason,
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_data)

    def test_get_corporation_journal_api_single_ref_types_empty(self):
        self.client.force_login(self.user)
        url = (
            "/ledger/api/corporation/2001/wallet/?type_refs=12341234,,1234,1234,,,2134"
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_corporation_journal_api_no_permission(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/corporation/2001/wallet/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
