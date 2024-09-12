from typing import Optional

from ninja import NinjaAPI

from django.db.models import Q
from django.test import TestCase

from app_utils.testing import create_user_from_evecharacter

from ledger import app_settings
from ledger.api.character.journal import LedgerJournalApiEndpoints
from ledger.api.schema import Character
from ledger.models.characteraudit import CharacterWalletJournalEntry
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all


class ManageApiJournalCharEndpointsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()

        cls.user, _ = create_user_from_evecharacter(
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
        cls.api = NinjaAPI()
        cls.manage_api_endpoints = LedgerJournalApiEndpoints(api=cls.api)

    def test_get_character_journal_api(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/0/wallet/"

        response = self.client.get(url)

        journal_query = CharacterWalletJournalEntry.objects.filter(
            character__character__character_id=1001
        ).select_related("first_party", "second_party")
        expected_data = []
        for journal in journal_query:
            expected_data.append(
                {
                    "character": dict(
                        Character(**journal.character.character.__dict__)
                    ),
                    "id": journal.entry_id,
                    "date": journal.date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "first_party": {
                        "id": (journal.first_party.eve_id),
                        "name": journal.first_party.name,
                        "cat": journal.first_party.category,
                    },
                    "second_party": {
                        "id": (journal.second_party.eve_id),
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

    def test_get_character_journal_api_single(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/1001/wallet/"

        journal_query = CharacterWalletJournalEntry.objects.filter(
            character__character__character_id=1001
        ).select_related("first_party", "second_party")

        response = self.client.get(url)

        expected_data = []
        for journal in journal_query:
            expected_data.append(
                {
                    "character": dict(
                        Character(**journal.character.character.__dict__)
                    ),
                    "id": journal.entry_id,
                    "date": journal.date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "first_party": {
                        "id": (journal.first_party.eve_id),
                        "name": journal.first_party.name,
                        "cat": journal.first_party.category,
                    },
                    "second_party": {
                        "id": (journal.second_party.eve_id),
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

    def test_get_character_journal_api_single_ref_types(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/1001/wallet/?type_refs=bounty_prizes,player_donation,contract_reward,transaction_tax,industry_job_tax,market_escrow,insurance"

        journal_query = CharacterWalletJournalEntry.objects.filter(
            character__character__character_id=1001
        ).select_related("first_party", "second_party")

        response = self.client.get(url)

        expected_data = []
        for journal in journal_query:
            expected_data.append(
                {
                    "character": dict(
                        Character(**journal.character.character.__dict__)
                    ),
                    "id": journal.entry_id,
                    "date": journal.date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "first_party": {
                        "id": (journal.first_party.eve_id),
                        "name": journal.first_party.name,
                        "cat": journal.first_party.category,
                    },
                    "second_party": {
                        "id": (journal.second_party.eve_id),
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

    def test_get_character_journal_api_single_ref_types_empty(self):
        self.client.force_login(self.user)
        url = "/ledger/api/account/1001/wallet/?type_refs=12341234,,1234,1234,,,2134"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_character_journal_api_no_permission(self):
        self.client.force_login(self.user2)
        url = "/ledger/api/account/1001/wallet/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
