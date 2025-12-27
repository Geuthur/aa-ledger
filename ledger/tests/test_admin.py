# Standard Library
from unittest.mock import patch

# Django
from django.contrib.admin.sites import AdminSite
from django.test import override_settings
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.evelinks import eveimageserver

# AA Ledger
from ledger.admin import (
    CharacterAuditAdmin,
    CharacterUpdateStatusAdminInline,
    CorporationAuditAdmin,
    CorporationUpdateStatusAdminInline,
)
from ledger.models.characteraudit import CharacterOwner, CharacterUpdateStatus
from ledger.models.corporationaudit import CorporationOwner, CorporationUpdateStatus
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import (
    add_owner_to_user,
    create_update_status,
)

ADMIN_PATH = "ledger.admin"


class MockRequest:
    pass


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestCorporationAuditAdmin(LedgerTestCase):
    """Test Backend AA Administration for Ledger."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.site = AdminSite()

        cls.corporation_audit_admin = CorporationAuditAdmin(CorporationOwner, cls.site)
        cls.corporation_audit = add_owner_to_user(
            cls.user,
            cls.user_character.character.character_id,
            owner_type="corporation",
        )

        cls.update_status = create_update_status(
            owner=cls.corporation_audit,
            section="wallet_journal",
            owner_type="corporation",
            last_update_at=timezone.now() - timezone.timedelta(minutes=5),
            last_update_finished_at=timezone.now() - timezone.timedelta(minutes=3),
            last_run_at=timezone.now() - timezone.timedelta(minutes=4),
            last_run_finished_at=timezone.now() - timezone.timedelta(minutes=2),
        )

    def test_get_queryset(self):
        """
        Test get_queryset method.

        This test ensures that the get_queryset method of the CorporationAuditAdmin
        class returns a valid queryset without errors.
        """
        # Test Action
        qs = self.corporation_audit_admin.get_queryset(CorporationOwner.objects.all())
        # Expected Result
        self.assertIsNotNone(qs)

    def test_run_update_duration(self):
        """
        Test run and update duration calculations in inline admin.

        This test verifies that the duration calculations for run and update times
        in the CorporationUpdateStatusAdminInline class are functioning correctly.
        """
        # Test Data
        inline = CorporationUpdateStatusAdminInline(CorporationUpdateStatus, self.site)

        # Test Action
        run_duration = inline._run_duration(self.update_status)
        update_duration = inline._update_duration(self.update_status).replace(
            "\xa0", " "
        )

        # Expected Results
        self.assertIn("minute", run_duration)
        self.assertIn("2 minutes", update_duration)
        self.assertEqual(inline._calc_duration(None, None), "-")

    @patch(ADMIN_PATH + ".update_corporation.delay")
    def test_force_update(self, mock_update_character_delay):
        """
        Test force_update admin action.

        This test checks that the force_update method in the CorporationAuditAdmin
        class correctly triggers the update_corporation task when invoked.
        """
        # Test Data
        request = self.factory.get("/")
        request.user = self.superuser

        self._middleware_process_request(request)
        queryset = CorporationOwner.objects.filter(pk=self.corporation_audit.pk)

        # Test Action
        self.corporation_audit_admin.force_update(request, queryset)

        # Expected Result
        mock_update_character_delay.assert_called_once()

    def test_entity_pic(self):
        """
        Test entity picture display in admin.

        This test verifies that the _entity_pic method in the CorporationAuditAdmin
        class returns the correct HTML for displaying the corporation's image.
        """
        # Test Data
        self.client.force_login(self.superuser)
        request = self.factory.get("/")
        request.user = self.superuser

        # Test Action/Expected Result
        expected_html = '<img src="{}" class="img-circle">'.format(
            eveimageserver._eve_entity_image_url(
                "corporation", self.corporation_audit.eve_corporation.corporation_id, 32
            )
        )
        self.assertEqual(
            self.corporation_audit_admin._entity_pic(self.corporation_audit),
            expected_html,
        )

    def test_corporation_corporation_id(self):
        """
        Test corporation ID display in admin.

        This test checks that the _corporation__corporation_id method in the
        CorporationAuditAdmin class returns the correct corporation ID.
        """
        # Test Data
        self.client.force_login(self.superuser)

        request = self.factory.get("/")
        request.user = self.superuser

        # Test Action/Expected Result
        self.assertEqual(
            self.corporation_audit_admin._corporation__corporation_id(
                self.corporation_audit
            ),
            2001,
        )

    def test_has_add_permission(self):
        """
        Test has_add_permission method.

        This test ensures that the has_add_permission method of the CorporationAuditAdmin
        class always returns False, preventing addition of new corporation audits
        """
        # Test Data
        self.client.force_login(self.superuser)
        request = self.factory.get("/")
        request.user = self.superuser

        # Test Action/Expected Result
        self.assertFalse(self.corporation_audit_admin.has_add_permission(request))

    def test_has_change_permission(self):
        """
        Test has_change_permission method.

        This test ensures that the has_change_permission method of the CorporationAuditAdmin
        class always returns False, preventing changes to existing corporation audits.
        """
        # Test Data
        self.client.force_login(self.superuser)
        request = self.factory.get("/")
        request.user = self.superuser

        # Test Action/Expected Result
        self.assertFalse(self.corporation_audit_admin.has_change_permission(request))
        self.assertFalse(
            self.corporation_audit_admin.has_change_permission(
                request, obj=self.corporation_audit
            )
        )


class TestCharacterAuditAdmin(LedgerTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.site = AdminSite()

        cls.character_audit_admin = CharacterAuditAdmin(CharacterOwner, cls.site)
        cls.character_audit = add_owner_to_user(
            cls.user,
            cls.user_character.character.character_id,
            owner_type="character",
        )
        cls.update_status = create_update_status(
            cls.character_audit,
            section="wallet_journal",
            last_update_at=timezone.now() - timezone.timedelta(minutes=5),
            last_update_finished_at=timezone.now() - timezone.timedelta(minutes=3),
            last_run_at=timezone.now() - timezone.timedelta(minutes=4),
            last_run_finished_at=timezone.now() - timezone.timedelta(minutes=2),
        )

    def test_get_queryset(self):
        qs = self.character_audit_admin.get_queryset(CharacterOwner.objects.all())
        self.assertIsNotNone(qs)

    @patch(ADMIN_PATH + ".update_character.delay")
    def test_force_update(self, mock_update_character_delay):
        """
        Test force_update admin action.

        This test checks that the force_update method in the CharacterAuditAdmin
        class correctly triggers the update_character task when invoked.
        """
        # Test Data
        queryset = CharacterOwner.objects.filter(pk=self.character_audit.pk)
        request = self.factory.get("/")
        request.user = self.superuser

        self._middleware_process_request(request)

        # Test Action
        self.character_audit_admin.force_update(request, queryset)

        # Expected Result
        mock_update_character_delay.assert_called_once()

    def test_run_update_duration(self):
        """
        Test run and update duration calculations in inline admin.

        This test verifies that the duration calculations for run and update times
        in the CharacterUpdateStatusAdminInline class are functioning correctly.
        """
        # Test Data
        inline = CharacterUpdateStatusAdminInline(CharacterUpdateStatus, self.site)

        # Test Action
        run_duration = inline._run_duration(self.update_status)
        update_duration = inline._update_duration(self.update_status).replace(
            "\xa0", " "
        )

        # Expected Results
        self.assertIn("minute", run_duration)
        self.assertIn("2 minutes", update_duration)
        self.assertEqual(inline._calc_duration(None, None), "-")

    def test_entity_pic(self):
        """
        Test entity picture rendering in admin.

        This test verifies that the _entity_pic method in the CharacterAuditAdmin
        class returns the correct HTML for displaying the character's image.
        """
        # Test Data
        self.client.force_login(self.superuser)

        # Test Action/Expected Result
        expected_html = '<img src="{}" class="img-circle">'.format(
            eveimageserver._eve_entity_image_url(
                "character", self.character_audit.eve_character.character_id, 32
            )
        )
        self.assertEqual(
            self.character_audit_admin._entity_pic(self.character_audit), expected_html
        )

    def test_character_character_name(self):
        """
        Test character name display in admin.

        This test checks that the _eve_character__character_name method in the
        CharacterAuditAdmin class returns the correct character name.
        """
        # Test Data
        self.client.force_login(self.superuser)

        # Test Action/Expected Result
        self.assertEqual(
            self.character_audit_admin._eve_character__character_name(
                self.character_audit
            ),
            self.character_audit.eve_character.character_name,
        )

    def test_has_add_permission(self):
        """
        Test has_add_permission method.

        This test ensures that the has_add_permission method of the CharacterAuditAdmin
        class always returns False, preventing addition of new character audits.
        """
        # Test Data
        request = self.factory.get("/")
        request.user = self.superuser

        # Test Action/Expected Result
        self.assertFalse(self.character_audit_admin.has_add_permission(request))

    def test_has_change_permission(self):
        """
        Test has_change_permission method.

        This test ensures that the has_change_permission method of the CharacterAuditAdmin
        class always returns False, preventing changes to existing character audits.
        """
        # Test Data
        request = self.factory.get("/")
        request.user = self.superuser

        # Test Action/Expected Result
        self.assertFalse(self.character_audit_admin.has_change_permission(request))
        self.assertFalse(
            self.character_audit_admin.has_change_permission(
                request, obj=self.character_audit
            )
        )
