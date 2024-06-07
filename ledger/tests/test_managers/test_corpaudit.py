from unittest.mock import patch

from django.test import TestCase

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import add_character_to_user, create_user_from_evecharacter

from ledger.models.corporationaudit import CorporationAudit
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_corp_audit

MODULE_PATH = "ledger.managers.corpaudit_manager"  # Replace with the actual module path


class CorpAuditQuerySetTest(TestCase):
    @classmethod
    def setUp(self):
        load_allianceauth()
        load_corp_audit()

    def test_visible_to_superuser(self):
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
        )
        self.user.is_superuser = True
        self.user.save()

        # Call the visible_to method with the superuser
        result = CorporationAudit.objects.visible_to(self.user)

        # Check that all CorporationAudit objects are returned
        expected_result = CorporationAudit.objects.all()
        self.assertEqual(list(result), list(expected_result))

    def test_visible_to_corp_audit_admin(self):
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.corp_audit_admin_access",
            ],
        )

        expected_result = CorporationAudit.objects.all()

        result = CorporationAudit.objects.visible_to(self.user)
        self.assertEqual(list(result), list(expected_result))

    def test_visible_to_admin_access(self):
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.admin_access",
            ],
        )

        self.assertTrue(self.user.has_perm("ledger.admin_access"))
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.has_perm("ledger.corp_audit_admin_access"))

        expected_result = CorporationAudit.objects.all()

        result = CorporationAudit.objects.visible_to(self.user)
        self.assertEqual(list(result), list(expected_result))

    def test_visible_to_corp_manager_access(self):
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.corp_audit_manager",
            ],
        )

        expected_result = CorporationAudit.objects.filter(id=1)

        result = CorporationAudit.objects.visible_to(self.user)
        self.assertEqual(list(result), list(expected_result))

    def test_visible_to_error(self):
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
            ],
        )
        self.user.profile.main_character = None

        result = list(
            CorporationAudit.objects.visible_to(self.user).values_list(
                "corporation_id", flat=True
            )
        )
        self.assertEqual(result, [])

    def test_visible_to_no_access(self):
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
        )

        result = list(
            CorporationAudit.objects.visible_to(self.user).values_list(
                "corporation_id", flat=True
            )
        )
        self.assertEqual(result, [])
