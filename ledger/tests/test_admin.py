# Django
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

# Alliance Auth
from allianceauth.eveonline.evelinks import eveimageserver

# Alliance Auth (External Libs)
from app_utils.testdata_factories import UserFactory

# AA Ledger
from ledger.admin import CharacterAuditAdmin, CorporationAuditAdmin
from ledger.models.characteraudit import CharacterAudit
from ledger.models.corporationaudit import CorporationAudit
from ledger.tests.testdata.generate_characteraudit import (
    add_characteraudit_character_to_user,
)
from ledger.tests.testdata.generate_corporationaudit import (
    add_corporationaudit_corporation_to_user,
    create_user_from_evecharacter,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth


class MockRequest:
    pass


class TestCorporationAuditAdmin(TestCase):
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


class TestCharacterAuditAdmin(TestCase):
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
            self.character_audit_admin._character__character_name(self.character_audit),
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
