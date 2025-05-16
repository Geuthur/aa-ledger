# Standard Library
from unittest.mock import patch

# Django
from django.test import override_settings
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests.testdata.esi_stub import esi_client_stub
from ledger.tests.testdata.generate_corporationaudit import (
    create_corporationaudit_from_user,
    create_user_from_evecharacter,
)
from ledger.tests.testdata.generate_walletjournal import (
    create_division,
    create_wallet_journal_entry,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.managers.corporation_journal_manager"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch(MODULE_PATH + ".etag_results")
@patch("ledger.models.general.EveEntity")
class TestCharacterJournalManager(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
        )
        cls.audit = create_corporationaudit_from_user(cls.user)

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=2001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1001)

        cls.division = create_division(
            corporation=cls.audit, name="MEGA KONTO", balance=1000000, division_id=1
        )

        cls.journal_entry = create_wallet_journal_entry(
            journal_type="corporation",
            division=cls.division,
            context_id=1,
            entry_id=10,
            amount=1000,
            balance=2000,
            date=timezone.datetime.replace(
                timezone.now(),
                year=2016,
                month=10,
                day=29,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
            description="Test Journal",
            first_party=cls.eve_character_first_party,
            second_party=cls.eve_character_second_party,
            ref_type="player_donation",
        )

    def test_update_wallet_journal(self, mock_eveentity, mock_etag, mock_esi):
        # given
        mock_esi.client = esi_client_stub
        mock_etag.return_value = [
            {
                "amount": 1000,
                "balance": 2000,
                "context_id": 1,
                "context_id_type": "test_id",
                "date": "2016-10-29T14:00:00Z",
                "description": "Test Journal",
                "first_party_id": 2001,
                "id": 10,
                "reason": "Test Reason",
                "ref_type": "player_donation",
                "second_party_id": 1001,
                "tax": 0,
                "tax_receiver_id": 0,
            },
            {
                "amount": 5000,
                "balance": 10000,
                "context_id": 2,
                "context_id_type": "bounty_id",
                "date": "2016-12-01T14:00:00Z",
                "description": "Bounty Tax",
                "first_party_id": 1001,
                "id": 13,
                "reason": "Bounty",
                "ref_type": "bounty_prizes",
                "second_party_id": 2001,
                "tax": 0,
                "tax_receiver_id": 0,
            },
            {
                "amount": 10000,
                "balance": 20000,
                "context_id": 4,
                "context_id_type": "missing_id",
                "date": "2016-12-01T14:00:00Z",
                "description": "Unknown Second Party",
                "first_party_id": 1001,
                "id": 16,
                "reason": "Second party unknown",
                "ref_type": "missing_party",
                "second_party_id": 9998,
                "tax": 0,
                "tax_receiver_id": 0,
            },
        ]

        mock_eveentity.objects.create_bulk_from_esi.return_value = True

        EveEntity.objects.create(
            eve_id=9998, name="Test Character 2", category="character"
        )

        self.audit.update_wallet_journal(force_refresh=False)

        self.assertSetEqual(
            set(
                self.division.ledger_corporation_journal.values_list(
                    "entry_id", flat=True
                )
            ),
            {10, 13, 16},
        )
        obj = self.division.ledger_corporation_journal.get(entry_id=10)
        self.assertEqual(obj.amount, 1000)
        self.assertEqual(obj.context_id, 1)
        self.assertEqual(obj.first_party.eve_id, 2001)
        self.assertEqual(obj.second_party.eve_id, 1001)

        obj = self.division.ledger_corporation_journal.get(entry_id=13)
        self.assertEqual(obj.amount, 5000)

        obj = self.division.ledger_corporation_journal.get(entry_id=16)
        self.assertEqual(obj.amount, 10000)
