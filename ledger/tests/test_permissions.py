"""Tests for centralized Ledger permissions on General model."""

# Django
from django.contrib.auth.models import AnonymousUser

# AA Ledger
from ledger.models.general import General
from ledger.tests import AuthTestCase
from ledger.tests.testdata.factory import UserMainFactory


class TestGeneralPermissions(AuthTestCase):
    def test_choices_should_return_all_seven_permissions(self):
        # Test Data
        expected_codenames = {
            "basic_access",
            "advanced_access",
            "manage_access",
            "char_audit_manager",
            "char_audit_admin_manager",
            "corp_audit_manager",
            "corp_audit_admin_manager",
        }

        # Test Action
        choices = General.Permission.choices
        codenames = {c[0] for c in choices}

        # Expected Result
        self.assertEqual(len(choices), 7)
        self.assertEqual(codenames, expected_codenames)

    def test_get_perm_should_return_prefixed_permission_string(self):
        # Test Data
        perm = General.Permission.BASIC_ACCESS

        # Test Action
        full_name = General.get_perm(perm)

        # Expected Result
        self.assertEqual(full_name, "ledger.basic_access")

    def test_has_perm_should_return_true_when_user_has_permission(self):
        # Test Data
        user = self.user

        # Test Action
        result = General.has_perm(user, General.Permission.BASIC_ACCESS)

        # Expected Result
        self.assertTrue(result)

    def test_has_perm_should_return_false_when_user_lacks_permission(self):
        # Test Data
        user = self.user

        # Test Action
        result = General.has_perm(user, General.Permission.CHAR_AUDIT_ADMIN_MANAGER)

        # Expected Result
        self.assertFalse(result)

    def test_has_any_perm_should_return_true_when_at_least_one_perm_is_held(self):
        # Test Data
        user = self.user

        # Test Action
        result = General.has_any_perm(
            user,
            General.Permission.CHAR_AUDIT_ADMIN_MANAGER,
            General.Permission.BASIC_ACCESS,
        )

        # Expected Result
        self.assertTrue(result)

    def test_has_any_perm_should_return_false_when_none_are_held(self):
        # Test Data
        user = self.user

        # Test Action
        result = General.has_any_perm(
            user,
            General.Permission.CHAR_AUDIT_ADMIN_MANAGER,
            General.Permission.CORP_AUDIT_ADMIN_MANAGER,
        )

        # Expected Result
        self.assertFalse(result)

    def test_has_management_access_should_return_true_for_superuser(self):
        # Test Data
        user = self.superuser

        # Test Action
        result = General.has_management_access(user)

        # Expected Result
        self.assertTrue(result)

    def test_has_management_access_should_return_true_for_manage_own_user(self):
        # Test Data
        user = self.manage_own_user

        # Test Action
        result = General.has_management_access(user)

        # Expected Result
        self.assertTrue(result)

    def test_has_management_access_should_return_false_for_regular_user(self):
        # Test Data
        user = self.user

        # Test Action
        result = General.has_management_access(user)

        # Expected Result
        self.assertFalse(result)

    def test_has_management_access_should_return_false_for_anonymous_user(self):
        # Test Data
        anon = AnonymousUser()

        # Test Action
        result = General.has_management_access(anon)

        # Expected Result
        self.assertFalse(result)

    def test_has_admin_management_access_should_return_true_for_superuser(self):
        # Test Data
        user = self.superuser

        # Test Action
        result = General.has_admin_management_access(user)

        # Expected Result
        self.assertTrue(result)

    def test_has_admin_management_access_should_return_true_for_admin_manager(self):
        # Test Data
        admin_manager_user = UserMainFactory(
            permissions__=[
                General.get_perm(General.Permission.CHAR_AUDIT_ADMIN_MANAGER)
            ]
        )

        # Test Action
        result = General.has_admin_management_access(admin_manager_user)

        # Expected Result
        self.assertTrue(result)

    def test_has_admin_management_access_should_return_false_for_corp_audit_manager(
        self,
    ):
        # Test Data
        user = self.manage_own_user

        # Test Action
        result = General.has_admin_management_access(user)

        # Expected Result
        self.assertFalse(result)

    def test_has_admin_management_access_should_return_false_for_anonymous_user(self):
        # Test Data
        anon = AnonymousUser()

        # Test Action
        result = General.has_admin_management_access(anon)

        # Expected Result
        self.assertFalse(result)

    def test_has_delete_access_should_return_true_for_superuser(self):
        # Test Data
        user = self.superuser

        # Test Action
        char_result = General.has_delete_access("character", user)
        corp_result = General.has_delete_access("corporation", user)

        # Expected Result
        self.assertTrue(char_result)
        self.assertTrue(corp_result)

    def test_has_delete_access_should_follow_admin_manager_permissions(self):
        # Test Data
        user = UserMainFactory(
            permissions__=[
                General.get_perm(General.Permission.CHAR_AUDIT_ADMIN_MANAGER)
            ]
        )

        # Test Action
        char_result = General.has_delete_access("character", user)
        corp_result = General.has_delete_access("corporation", user)

        # Expected Result
        self.assertTrue(char_result)
        self.assertFalse(corp_result)

    def test_has_delete_access_should_return_false_for_anonymous_user(self):
        # Test Data
        anon = AnonymousUser()

        # Test Action
        result = General.has_delete_access("character", anon)

        # Expected Result
        self.assertFalse(result)
