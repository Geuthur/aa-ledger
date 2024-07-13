from django.test import RequestFactory, TestCase

from allianceauth.eveonline.models import EveCorporationInfo
from app_utils.testing import create_user_from_evecharacter

from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletJournalEntry,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all

MODULE_PATH = "ledger.models.general"


class TestCorporationAuditModel(TestCase):
    def setUp(self):
        load_allianceauth()
        self.audit = CorporationAudit(
            corporation=EveCorporationInfo.objects.get(corporation_id=2001)
        )

    def test_str(self):
        self.assertEqual(str(self.audit), "Hell RiderZ's Corporation Data")


class TestCorporationWalletJournal(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()
        cls.journal = CorporationWalletJournalEntry.objects.get(entry_id=1)

    def test_str(self):
        self.assertEqual(
            str(self.journal),
            "Corporation Wallet Journal: CONCORD 'ess_escrow_transfer' Gneuten: 100000.00 isk",
        )

    def test_get_visible(self):
        self.factory = RequestFactory()
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.corp_audit_admin_manager",
            ],
        )
        request = self.factory.get("/")
        request.user = self.user

        query = CorporationWalletJournalEntry.get_visible(request.user)

        excepted_corporation = CorporationWalletJournalEntry.objects.all()

        self.assertEqual(list(query), list(excepted_corporation))
