# Django
from django.contrib.auth.models import Permission
from django.test import TestCase

# Alliance Auth
from allianceauth.tests.auth_utils import AuthUtils

# AA Ledger
from ledger.models.corporationaudit import CorporationAudit
from ledger.tests.testdata.generate_corporationaudit import (
    create_corporationaudit_from_user,
    create_user_from_evecharacter,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth

MODULE_PATH = "ledger.models.corporationaudit"


class TestCorporationAuditModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001, permissions=["ledger.basic_access"]
        )
        cls.user2, cls.character_ownership2 = create_user_from_evecharacter(
            1002, permissions=["ledger.basic_access"]
        )
        cls.audit = create_corporationaudit_from_user(cls.user)
        cls.audit2 = create_corporationaudit_from_user(cls.user2)

    def test_str(self):
        expected_str = CorporationAudit.objects.get(id=self.audit.pk)
        self.assertEqual(self.audit, expected_str)

    def test_get_esi_scopes(self):
        self.assertEqual(
            self.audit.get_esi_scopes(),
            [
                # General
                "esi-search.search_structures.v1",
                "esi-universe.read_structures.v1",
                "esi-characters.read_corporation_roles.v1",
                # Mining
                "esi-industry.read_corporation_mining.v1",
                # wallets
                "esi-wallet.read_corporation_wallets.v1",
                "esi-markets.read_corporation_orders.v1",
                "esi-industry.read_corporation_jobs.v1",
                "esi-corporations.read_divisions.v1",
            ],
        )

    def test_access_no_perms(self):
        corporation = CorporationAudit.objects.visible_to(self.user)
        self.assertNotIn(self.audit, corporation)
        self.assertNotIn(self.audit2, corporation)

    def test_access_perms_own_corp(self):
        self.user = AuthUtils.add_permission_to_user_by_name(
            "ledger.advanced_access", self.user
        )
        self.user.refresh_from_db()
        corporation = CorporationAudit.objects.visible_to(self.user)
        self.assertIn(self.audit, corporation)
        self.assertNotIn(self.audit2, corporation)
