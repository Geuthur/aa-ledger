# Standard Library
from unittest.mock import Mock, patch

# Django
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, override_settings
from django.utils import timezone
from django.utils.safestring import mark_safe

# Alliance Auth
from allianceauth.eveonline.evelinks import eveimageserver

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase

# AA Ledger
from ledger.admin import (
    CharacterAuditAdmin,
    CharacterUpdateStatusAdminInline,
    CorporationAuditAdmin,
    CorporationUpdateStatusAdminInline,
)
from ledger.models.characteraudit import CharacterAudit, CharacterUpdateStatus
from ledger.models.corporationaudit import CorporationAudit, CorporationUpdateStatus
from ledger.tests.testdata.generate_characteraudit import (
    add_characteraudit_character_to_user,
    create_update_status,
)
from ledger.tests.testdata.generate_corporationaudit import (
    add_corporationaudit_corporation_to_user,
    create_corporation_update_status,
    create_user_from_evecharacter,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth

ADMIN_PATH = "ledger.admin"


class MockRequest:
    pass


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestCorporationAuditAdmin(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()

        cls.factory = RequestFactory()
        cls.site = AdminSite()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            ["ledger.basic_access"],
        )
        cls.corporation_audit_admin = CorporationAuditAdmin(CorporationAudit, cls.site)
        cls.corporation_audit = add_corporationaudit_corporation_to_user(
            cls.user,
            cls.character_ownership.character.character_id,
        )
        cls.user.is_superuser = True

        cls.update_status = create_corporation_update_status(
            cls.corporation_audit,
            section="wallet_journal",
            last_update_at=timezone.now() - timezone.timedelta(minutes=5),
            last_update_finished_at=timezone.now() - timezone.timedelta(minutes=3),
            last_run_at=timezone.now() - timezone.timedelta(minutes=4),
            last_run_finished_at=timezone.now() - timezone.timedelta(minutes=2),
        )

    def test_get_queryset(self):
        qs = self.corporation_audit_admin.get_queryset(CorporationAudit.objects.all())
        self.assertIsNotNone(qs)

    def test_run_update_duration(self):
        inline = CorporationUpdateStatusAdminInline(CorporationUpdateStatus, self.site)

        run_duration = inline._run_duration(self.update_status)
        update_duration = inline._update_duration(self.update_status).replace(
            "\xa0", " "
        )
        self.assertIn("minute", run_duration)
        self.assertIn("2 minutes", update_duration)
        self.assertEqual(inline._calc_duration(None, None), "-")

    @patch(ADMIN_PATH + ".update_corporation.delay")
    def test_force_update(self, mock_update_character_delay):
        request = self.factory.get("/")
        request.user = self.user

        # Add session middleware to process the request
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        message_middleware = MessageMiddleware(Mock())
        message_middleware.process_request(request)

        queryset = CorporationAudit.objects.filter(pk=self.corporation_audit.pk)
        self.corporation_audit_admin.force_update(request, queryset)
        mock_update_character_delay.assert_called_once()

    def test_entity_pic(self):
        self.client.force_login(self.user)
        request = self.factory.get("/")
        request.user = self.user
        expected_html = '<img src="{}" class="img-circle">'.format(
            eveimageserver._eve_entity_image_url(
                "corporation", self.corporation_audit.corporation.corporation_id, 32
            )
        )
        self.assertEqual(
            self.corporation_audit_admin._entity_pic(self.corporation_audit),
            expected_html,
        )

    def test_corporation_corporation_id(self):
        self.client.force_login(self.user)
        request = self.factory.get("/")
        request.user = self.user
        self.assertEqual(
            self.corporation_audit_admin._corporation__corporation_id(
                self.corporation_audit
            ),
            2001,
        )

    def test_has_add_permission(self):
        self.client.force_login(self.user)
        request = self.factory.get("/")
        request.user = self.user
        self.assertFalse(self.corporation_audit_admin.has_add_permission(request))

    def test_has_change_permission(self):
        self.client.force_login(self.user)
        request = self.factory.get("/")
        request.user = self.user
        request = MockRequest()
        self.assertFalse(self.corporation_audit_admin.has_change_permission(request))
        self.assertFalse(
            self.corporation_audit_admin.has_change_permission(
                request, obj=self.corporation_audit
            )
        )


class TestCharacterAuditAdmin(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        cls.factory = RequestFactory()
        cls.site = AdminSite()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            ["ledger.basic_access"],
        )
        cls.character_audit_admin = CharacterAuditAdmin(CharacterAudit, cls.site)
        cls.character_audit = add_characteraudit_character_to_user(
            cls.user,
            cls.character_ownership.character.character_id,
        )
        cls.user.is_superuser = True
        cls.update_status = create_update_status(
            cls.character_audit,
            section="wallet_journal",
            last_update_at=timezone.now() - timezone.timedelta(minutes=5),
            last_update_finished_at=timezone.now() - timezone.timedelta(minutes=3),
            last_run_at=timezone.now() - timezone.timedelta(minutes=4),
            last_run_finished_at=timezone.now() - timezone.timedelta(minutes=2),
        )

    def test_get_queryset(self):
        qs = self.character_audit_admin.get_queryset(CharacterAudit.objects.all())
        self.assertIsNotNone(qs)

    @patch(ADMIN_PATH + ".update_character.delay")
    def test_force_update(self, mock_update_character_delay):
        queryset = CharacterAudit.objects.filter(pk=self.character_audit.pk)
        request = self.factory.get("/")

        # Add session middleware to process the request
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        message_middleware = MessageMiddleware(Mock())
        message_middleware.process_request(request)

        self.character_audit_admin.force_update(request, queryset)
        mock_update_character_delay.assert_called_once()

    def test_run_update_duration(self):
        inline = CharacterUpdateStatusAdminInline(CharacterUpdateStatus, self.site)

        run_duration = inline._run_duration(self.update_status)
        update_duration = inline._update_duration(self.update_status).replace(
            "\xa0", " "
        )
        self.assertIn("minute", run_duration)
        self.assertIn("2 minutes", update_duration)
        self.assertEqual(inline._calc_duration(None, None), "-")

    def test_entity_pic(self):
        self.client.force_login(self.user)
        expected_html = '<img src="{}" class="img-circle">'.format(
            eveimageserver._eve_entity_image_url(
                "character", self.character_audit.eve_character.character_id, 32
            )
        )
        self.assertEqual(
            self.character_audit_admin._entity_pic(self.character_audit), expected_html
        )

    def test_character_character_name(self):
        self.assertEqual(
            self.character_audit_admin._eve_character__character_name(
                self.character_audit
            ),
            self.character_audit.eve_character.character_name,
        )

    def test_has_add_permission(self):
        request = self.factory.get("/")
        self.assertFalse(self.character_audit_admin.has_add_permission(request))

    def test_has_change_permission(self):
        request = self.factory.get("/")
        self.assertFalse(self.character_audit_admin.has_change_permission(request))
        self.assertFalse(
            self.character_audit_admin.has_change_permission(
                request, obj=self.character_audit
            )
        )
