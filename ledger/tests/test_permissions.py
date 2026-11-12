"""Tests for the permission definitions in General."""

# Standard Library
import re
from pathlib import Path

# Django
from django.contrib.auth.models import AnonymousUser

# AA Ledger
import ledger
from ledger.models.general import General
from ledger.tests import AuthTestCase
from ledger.tests.testdata.factory import UserMainFactory
from ledger.tests.testdata.users import create_manage_own_user

APP_LABEL = "ledger"
# Permission strings like "<app_label>.<codename>" in quotes, any app label
PERMISSION_PATTERN = re.compile(
    r"[\"']([A-Za-z0-9_]+)\.([A-Za-z0-9_]*_(?:access|manager))[\"']"
)
IGNORED_PARTS = ("tests", "migrations", "node_modules")
SCANNED_SUFFIXES = (".py", ".html", ".txt")


class TestGeneralPermissions(AuthTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manage_own_user = create_manage_own_user()

    def test_codenames_should_stay_unchanged(self):
        self.assertEqual(
            [codename for codename, _ in General._meta.permissions],
            [
                "basic_access",
                "advanced_access",
                "manage_access",
                "char_audit_manager",
                "char_audit_admin_manager",
                "corp_audit_manager",
                "corp_audit_admin_manager",
            ],
        )

    def test_used_permission_strings_should_exist_in_general(self):
        """Every permission string used in code and templates is defined in General.Meta.permissions."""
        defined = {f"{APP_LABEL}.{c}" for c, _ in General._meta.permissions}
        used: dict[str, set[str]] = {}
        root = Path(ledger.__file__).parent

        for path in root.rglob("*"):
            relative = path.relative_to(root)
            if path.suffix not in SCANNED_SUFFIXES or any(
                part in IGNORED_PARTS for part in relative.parts
            ):
                continue
            for label, codename in PERMISSION_PATTERN.findall(path.read_text("utf-8")):
                used.setdefault(f"{label}.{codename}", set()).add(str(relative))

        self.assertTrue(used, "No permission strings found, pattern is broken.")
        unknown = {c: sorted(f) for c, f in used.items() if c not in defined}
        self.assertEqual(unknown, {})

    def test_has_management_access_should_return_true_for_superuser(self):
        self.assertTrue(General.objects.has_management_access(self.superuser))

    def test_has_management_access_should_return_true_for_manage_own_user(self):
        self.assertTrue(General.objects.has_management_access(self.manage_own_user))

    def test_has_management_access_should_return_false_for_regular_user(self):
        self.assertFalse(General.objects.has_management_access(self.user))

    def test_has_management_access_should_return_false_for_anonymous_user(self):
        self.assertFalse(General.objects.has_management_access(AnonymousUser()))

    def test_has_admin_management_access_should_return_true_for_superuser(self):
        self.assertTrue(General.objects.has_admin_management_access(self.superuser))

    def test_has_admin_management_access_should_return_true_for_admin_manager(self):
        user = UserMainFactory(permissions__=["ledger.char_audit_admin_manager"])
        self.assertTrue(General.objects.has_admin_management_access(user))

    def test_has_admin_management_access_should_return_false_for_corp_audit_manager(
        self,
    ):
        self.assertFalse(
            General.objects.has_admin_management_access(self.manage_own_user)
        )

    def test_has_admin_management_access_should_return_false_for_anonymous_user(self):
        self.assertFalse(General.objects.has_admin_management_access(AnonymousUser()))

    def test_has_delete_access_should_return_true_for_superuser(self):
        self.assertTrue(General.objects.has_delete_access("character", self.superuser))
        self.assertTrue(
            General.objects.has_delete_access("corporation", self.superuser)
        )

    def test_has_delete_access_should_follow_admin_manager_permissions(self):
        user = UserMainFactory(permissions__=["ledger.char_audit_admin_manager"])
        self.assertTrue(General.objects.has_delete_access("character", user))
        self.assertFalse(General.objects.has_delete_access("corporation", user))

    def test_has_delete_access_should_return_false_for_anonymous_user(self):
        self.assertFalse(
            General.objects.has_delete_access("character", AnonymousUser())
        )
