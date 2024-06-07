from django.test import RequestFactory, TestCase

from allianceauth.eveonline.models import EveCorporationInfo
from app_utils.testing import create_user_from_evecharacter

from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletJournalEntry,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_corp_audit, load_corp_journal

MODULE_PATH = "ledger.models.general"  # replace with your actual module path


class TestCorporationAuditModel(TestCase):
    def setUp(self):
        load_allianceauth()
        self.audit = CorporationAudit(
            corporation=EveCorporationInfo.objects.get(corporation_id=2001)
        )

    def test_str(self):
        self.assertEqual(str(self.audit), "Hell RiderZ's Corporation Data")


class TestCorporationWalletJournal(TestCase):
    def setUp(self):
        load_allianceauth()
        load_corp_audit()
        load_corp_journal()
        self.journal = CorporationWalletJournalEntry.objects.get(id=1)

    def test_str(self):
        self.assertEqual(
            str(self.journal),
            "Corporation Wallet Journal: Gneuten 'test' rotze Rotineque: 100000.00 isk",
        )

    def test_get_visible(self):
        self.factory = RequestFactory()
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.corp_audit_admin_access",
            ],
        )
        request = self.factory.get("/")
        request.user = self.user

        query = CorporationWalletJournalEntry.get_visible(request.user)

        excepted_corporation = CorporationWalletJournalEntry.objects.all()

        self.assertEqual(list(query), list(excepted_corporation))
