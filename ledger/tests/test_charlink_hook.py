"""Tests for the permissions of the Charlink imports."""

# Standard Library
import importlib
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

# AA Ledger
from ledger.tests import AuthTestCase
from ledger.tests.testdata.factory import UserMainFactory

MODULE_PATH = "ledger.thirdparty.charlink_hook"


def _charlink_stub() -> dict[str, ModuleType]:
    """Stand-in for `charlink`, which is not installed in the test environment."""
    utils = ModuleType("charlink.app_imports.utils")
    utils.AppImport = lambda app_label, imports: SimpleNamespace(
        app_label=app_label, imports=imports
    )
    utils.LoginImport = lambda **kwargs: SimpleNamespace(**kwargs)
    return {
        "charlink": ModuleType("charlink"),
        "charlink.app_imports": ModuleType("charlink.app_imports"),
        "charlink.app_imports.utils": utils,
    }


class TestCharlinkHookAccess(AuthTestCase):
    """
    Basic access is only granted by `basic_access`.

    The corporation import does the same as the view `add_corp` and needs
    `basic_access` and `manage_access`; the character import needs `basic_access`.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with patch.dict(sys.modules, _charlink_stub()):
            sys.modules.pop(MODULE_PATH, None)
            cls.hook = importlib.import_module(MODULE_PATH)
        cls.addClassCleanup(sys.modules.pop, MODULE_PATH, None)
        imports = {
            login_import.unique_id: login_import
            for login_import in cls.hook.app_import.imports
        }
        cls.character_import = imports["default"]
        cls.corporation_import = imports["corpaudit"]

        cls.user_without_permission = UserMainFactory(permissions__=[])
        cls.user_manage_only = UserMainFactory(permissions__=["ledger.manage_access"])
        cls.user_basic_and_manage = UserMainFactory(
            permissions__=["ledger.basic_access", "ledger.manage_access"]
        )
        cls.superuser_without_permission = UserMainFactory(
            permissions__=[], is_superuser=True
        )

    def test_corporation_import_should_need_basic_and_manage_access(self):
        # Test Data: `self.user` has `basic_access` only
        expected = {
            self.user_without_permission: False,
            self.user: False,
            self.user_manage_only: False,
            self.user_basic_and_manage: True,
            self.superuser_without_permission: True,
        }

        for user, allowed in expected.items():
            with self.subTest(user=user.username):
                # Test Action
                result = self.corporation_import.check_permissions(user)

                # Expected Result
                self.assertEqual(result, allowed)

    def test_corporation_import_should_list_only_users_with_both_permissions(self):
        # Test Action
        users = set(self.corporation_import.get_users_with_perms())

        # Expected Result
        self.assertIn(self.user_basic_and_manage, users)
        self.assertIn(self.superuser_without_permission, users)
        self.assertNotIn(self.user_manage_only, users)
        self.assertNotIn(self.user, users)
        self.assertNotIn(self.user_without_permission, users)

    def test_character_import_should_need_basic_access(self):
        # Test Action and Expected Result
        self.assertTrue(self.character_import.check_permissions(self.user))
        self.assertFalse(self.character_import.check_permissions(self.user_manage_only))
