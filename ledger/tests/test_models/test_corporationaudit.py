from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from allianceauth.eveonline.models import EveCorporationInfo

from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletJournalEntry,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import (
    load_corp_audit,
    load_corp_journal,
    load_eveentity,
)

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
