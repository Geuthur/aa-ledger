from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from allianceauth.eveonline.evelinks import eveimageserver
from app_utils.testdata_factories import UserFactory

from ledger.admin import CharacterAuditAdmin, CorporationAuditAdmin
from ledger.models.characteraudit import CharacterAudit
from ledger.models.corporationaudit import CorporationAudit
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all


class MockRequest:
    pass


class TestCorporationAuditAdmin(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()
        cls.factory = RequestFactory()
        cls.site = AdminSite()
        cls.corporation_audit_admin = CorporationAuditAdmin(CorporationAudit, cls.site)
        cls.corporation_audit = CorporationAudit.objects.get(id=1)

    def test_entity_pic(self):
        user = UserFactory(is_superuser=True, is_staff=True)
        self.client.force_login(user)
        request = self.factory.get("/")
        request.user = user
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
        user = UserFactory(is_superuser=True, is_staff=True)
        self.client.force_login(user)
        request = self.factory.get("/")
        request.user = user
        self.assertEqual(
            self.corporation_audit_admin._corporation__corporation_id(
                self.corporation_audit
            ),
            2001,
        )

    def test_last_update_wallet(self):
        user = UserFactory(is_superuser=True, is_staff=True)
        self.client.force_login(user)
        request = self.factory.get("/")
        request.user = user
        self.assertEqual(
            self.corporation_audit_admin._last_update_wallet(self.corporation_audit),
            None,
        )

    def test_has_add_permission(self):
        user = UserFactory(is_superuser=True, is_staff=True)
        self.client.force_login(user)
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.corporation_audit_admin.has_add_permission(request))

    def test_has_change_permission(self):
        user = UserFactory(is_superuser=True, is_staff=True)
        self.client.force_login(user)
        request = self.factory.get("/")
        request.user = user
        request = MockRequest()
        self.assertFalse(self.corporation_audit_admin.has_change_permission(request))
        self.assertFalse(
            self.corporation_audit_admin.has_change_permission(
                request, obj=self.corporation_audit
            )
        )


class TestCharacterAuditAdmin(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Assuming load_allianceauth() and load_char_audit() are functions you've defined elsewhere to set up your test environment
        load_allianceauth()
        load_ledger_all()
        cls.factory = RequestFactory()
        cls.site = AdminSite()
        cls.character_audit_admin = CharacterAuditAdmin(CharacterAudit, cls.site)
        cls.character_audit = CharacterAudit.objects.get(id=1)

    def test_entity_pic(self):
        user = UserFactory(is_superuser=True, is_staff=True)
        self.client.force_login(user)
        expected_html = '<img src="{}" class="img-circle">'.format(
            eveimageserver._eve_entity_image_url(
                "character", self.character_audit.character.character_id, 32
            )
        )
        self.assertEqual(
            self.character_audit_admin._entity_pic(self.character_audit), expected_html
        )

    def test_character_character_name(self):
        self.assertEqual(
            self.character_audit_admin._character__character_name(self.character_audit),
            self.character_audit.character.character_name,
        )

    def test_last_update_wallet(self):
        self.assertEqual(
            self.character_audit_admin._last_update_wallet(self.character_audit),
            self.character_audit.last_update_wallet,
        )

    def test_last_update_mining(self):
        self.assertEqual(
            self.character_audit_admin._last_update_mining(self.character_audit),
            self.character_audit.last_update_mining,
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
