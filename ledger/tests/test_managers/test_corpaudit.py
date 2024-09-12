from django.db import models
from django.test import TestCase

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import add_character_to_user, create_user_from_evecharacter

from ledger.models.corporationaudit import CorporationAudit
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all

MODULE_PATH = "ledger.managers.corpaudit_manager"


class CorpAuditQuerySetTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()

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
                "ledger.corp_audit_admin_manager",
            ],
        )

        expected_result = CorporationAudit.objects.all()

        result = CorporationAudit.objects.visible_to(self.user)
        self.assertEqual(list(result), list(expected_result))

    def test_visible_to_advanced_access(self):
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.advanced_access",
            ],
        )
        add_character_to_user(self.user, EveCharacter.objects.get(character_id=1002))
        add_character_to_user(self.user, EveCharacter.objects.get(character_id=1003))

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

        result = (
            CorporationAudit.objects.visible_to(self.user)
            .values_list("corporation_id", flat=True)
            .count()
        )

        self.assertEqual(result, 0)

    def test_visible_to_no_access(self):
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
        )

        result = CorporationAudit.objects.visible_to(self.user).count()

        self.assertEqual(result, 0)
