from django.test import TestCase

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import create_user_from_evecharacter

from ledger.models.characteraudit import CharacterAudit, CharacterMiningLedger
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_char_audit, load_char_mining

MODULE_PATH = "ledger.managers.corpaudit_manager"  # Replace with the actual module path


class CharAuditQuerySetTest(TestCase):
    @classmethod
    def setUp(self):
        load_allianceauth()
        load_char_audit()
        load_char_mining()

    def test_visible_to_superuser(self):
        # given
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
        )
        self.user.is_superuser = True
        self.user.save()
        # when
        result = CharacterAudit.objects.visible_to(self.user)
        expected_result = CharacterAudit.objects.all()
        # then
        self.assertEqual(list(result), list(expected_result))
        # when
        expected_result = EveCharacter.objects.all()
        result = CharacterAudit.objects.visible_eve_characters(self.user)
        # then
        self.assertEqual(list(result), list(expected_result))

    def test_visible_to_char_audit_admin(self):
        # given
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.char_audit_admin_access",
            ],
        )
        # when
        expected_result = CharacterAudit.objects.all()
        result = CharacterAudit.objects.visible_to(self.user)
        # then
        self.assertEqual(list(result), list(expected_result))
        # when
        expected_result = EveCharacter.objects.all()
        result = CharacterAudit.objects.visible_eve_characters(self.user)
        # then
        self.assertEqual(list(result), list(expected_result))

    def test_visible_to_admin_access(self):
        # given
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.admin_access",
            ],
        )
        # when
        expected_result = CharacterAudit.objects.all()
        result = CharacterAudit.objects.visible_to(self.user)
        # then
        self.assertEqual(list(result), list(expected_result))
        # when
        expected_result = EveCharacter.objects.all()
        result = CharacterAudit.objects.visible_eve_characters(self.user)
        # then
        self.assertEqual(list(result), list(expected_result))

    def test_visible_to_char_audit_manager(self):
        # given
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.char_audit_manager",
            ],
        )
        # when
        expected_result = CharacterAudit.objects.filter(
            character__character_id__in=[1001, 1004, 1005, 1006]
        )
        result = CharacterAudit.objects.visible_to(self.user)
        # then
        self.assertEqual(list(result), list(expected_result))
        # when
        expected_result = EveCharacter.objects.filter(
            character_id__in=[1001, 1004, 1005, 1006]
        )
        result = CharacterAudit.objects.visible_eve_characters(self.user)
        # then
        self.assertEqual(list(result), list(expected_result))

    def test_visible_to_no_access(self):
        # given
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
        )
        # when
        expected_result = CharacterAudit.objects.filter(character__character_id=1001)
        result = CharacterAudit.objects.visible_to(self.user)
        # then
        self.assertEqual(list(result), list(expected_result))
        # when
        expected_result = EveCharacter.objects.filter(character_id=1001)
        result = CharacterAudit.objects.visible_eve_characters(self.user)
        # then
        self.assertEqual(list(result), list(expected_result))

    def test_visible_to_error(self):
        # given
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
            ],
        )
        self.user.profile.main_character = None
        # when
        expected_result = CharacterAudit.objects.filter(character__character_id=9999)
        result = CharacterAudit.objects.visible_to(self.user)
        # then
        self.assertEqual(list(result), list(expected_result))
        # when
        expected_result = EveCharacter.objects.filter(character_id=99999)
        result = CharacterAudit.objects.visible_eve_characters(self.user)
        # then
        self.assertEqual(list(result), list(expected_result))

    def test_annotate_pricing(self):
        # given
        self.user, self.character_ownership = create_user_from_evecharacter(
            1001,
        )
        # when
        expected_result = CharacterMiningLedger.objects.filter(
            character__character__character_id=1001
        )
        result = CharacterMiningLedger.objects.filter(
            character__character__character_id=1001
        ).annotate_pricing()
        # then
        self.assertEqual(list(result), list(expected_result))
