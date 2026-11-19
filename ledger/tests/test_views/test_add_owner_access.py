"""Tests that the views adding owners check the permissions before the SSO detour."""

# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse

# AA Ledger
from ledger.tests import AuthTestCase
from ledger.tests.testdata.factory import UserMainFactory

LOGIN_URL = "/account/login/"


class TestAddOwnerAccess(AuthTestCase):
    """
    Basic access is only granted by `basic_access`.

    `add_corp` and `add_ally` need `basic_access` and `manage_access`. A user
    without them is sent to the login page and never reaches `token_required`
    (SSO or token selection).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_without_permission = UserMainFactory(permissions__=[])
        cls.user_manage_only = UserMainFactory(permissions__=["ledger.manage_access"])
        cls.user_basic_and_manage = UserMainFactory(
            permissions__=["ledger.basic_access", "ledger.manage_access"]
        )

    def _get(self, user, url_name):
        self.client.force_login(user)
        return self.client.get(reverse(url_name))

    def _assert_denied(self, response):
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(response["Location"].startswith(LOGIN_URL))

    def _assert_sent_to_sso(self, response):
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(response["Location"].startswith(LOGIN_URL))
        self.assertIn("oauth", response["Location"])

    def test_add_corp_and_add_ally_should_deny_manage_access_without_basic_access(
        self,
    ):
        for url_name in ("ledger:add_corp", "ledger:add_ally"):
            with self.subTest(view=url_name):
                # Test Action
                response = self._get(self.user_manage_only, url_name)

                # Expected Result
                self._assert_denied(response)

    def test_add_corp_and_add_ally_should_deny_basic_access_without_manage_access(
        self,
    ):
        for url_name in ("ledger:add_corp", "ledger:add_ally"):
            with self.subTest(view=url_name):
                # Test Action
                response = self._get(self.user, url_name)

                # Expected Result
                self._assert_denied(response)

    def test_add_corp_and_add_ally_should_send_to_sso_with_both_permissions(self):
        for url_name in ("ledger:add_corp", "ledger:add_ally"):
            with self.subTest(view=url_name):
                # Test Action
                response = self._get(self.user_basic_and_manage, url_name)

                # Expected Result
                self._assert_sent_to_sso(response)

    def test_add_char_should_deny_without_basic_access(self):
        for user in (self.user_without_permission, self.user_manage_only):
            with self.subTest(user=user.username):
                # Test Action
                response = self._get(user, "ledger:add_char")

                # Expected Result
                self._assert_denied(response)

    def test_add_char_should_reach_token_required_with_basic_access(self):
        # Test Action
        response = self._get(self.user, "ledger:add_char")

        # Expected Result: the user already has tokens with the scopes, so
        # `token_required` shows its token selection
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "esi/select_token.html")
