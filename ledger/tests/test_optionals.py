from unittest.mock import MagicMock, call, patch

from django.db import IntegrityError
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import create_user_from_evecharacter

from ledger.tasks import create_member_audit
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all
from ledger.tests.testdata.load_planetary import load_planetary

MODULE_PATH = "ledger.tasks"


class TestTasks(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()
        load_planetary()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
            ],
        )

        cls.user2, cls.character_ownership2 = create_user_from_evecharacter(
            1002,
            permissions=[
                "ledger.basic_access",
            ],
        )

        cls.token = cls.user.token_set.first()
        cls.corporation = cls.character_ownership.character.corporation

    @patch(MODULE_PATH + ".CharacterAudit.objects.update_or_create")
    @patch(MODULE_PATH + ".EveCharacter.objects.get_character_by_id")
    @patch("memberaudit.models.Character.objects.all")
    @patch(MODULE_PATH + ".CharacterAudit.objects.all")
    def test_create_member_audit(
        self,
        mock_char_audit_all,
        mock_char_all,
        mock_get_character_by_id,
        mock_update_or_create,
    ):
        # Setup mock return values
        mock_char_audit_all.return_value.values_list.return_value = []
        mock_char_all.return_value.values_list.return_value = [1999]
        mock_get_character_by_id.return_value = EveCharacter(
            character_id=1999,
            character_name="Test Character",
            corporation_id=2001,
            corporation_name="Hell Rider'Z",
        )

        # Call the function
        create_member_audit()

        # Check that update_or_create was called
        mock_update_or_create.assert_called_once()

    @patch(MODULE_PATH + ".CharacterAudit.objects.update_or_create")
    @patch(MODULE_PATH + ".EveCharacter.objects.get_character_by_id")
    @patch("memberaudit.models.Character.objects.all")
    @patch(MODULE_PATH + ".CharacterAudit.objects.all")
    def test_create_member_audit_no_update_or_create(
        self,
        mock_char_audit_all,
        mock_char_all,
        mock_get_character_by_id,
        mock_update_or_create,
    ):
        # Setup mock return values
        mock_char_audit_all.return_value.values_list.return_value = [1, 2, 3, 4, 5]
        mock_char_all.return_value.values_list.return_value = [2, 3, 4, 5]

        # Call the function
        create_member_audit()

        # Check that update_or_create was not called
        mock_update_or_create.assert_not_called()

    @patch(MODULE_PATH + ".CharacterAudit.objects.update_or_create")
    @patch(MODULE_PATH + ".EveCharacter.objects.get_character_by_id")
    @patch("memberaudit.models.Character.objects.all")
    @patch(MODULE_PATH + ".CharacterAudit.objects.all")
    @patch(MODULE_PATH + ".logger")
    def test_create_member_audit_integrityerror(
        self,
        mock_logger,
        mock_char_audit_all,
        mock_char_all,
        mock_get_character_by_id,
        mock_update_or_create,
    ):
        # Setup mock return values
        mock_char_audit_all.return_value.values_list.return_value = [1, 2, 3, 4, 5]
        mock_char_all.return_value.values_list.return_value = [6, 7]
        mock_update_or_create.side_effect = IntegrityError
        # Call the function
        create_member_audit()

        mock_logger.debug.assert_called_once_with(
            "Created %s missing Member Audit Characters", 0
        )
