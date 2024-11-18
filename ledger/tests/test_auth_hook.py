from unittest.mock import MagicMock

from django.test import TestCase
from django.urls import reverse

from app_utils.testdata_factories import UserMainFactory

from ledger.auth_hooks import LedgerMenuItem, register_charlink_hook


class TestAuthHooks(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = UserMainFactory(permissions=["ledger.basic_access"])
        cls.html_menu = f"""
            <li class="d-flex flex-wrap m-2 p-2 pt-0 pb-0 mt-0 mb-0 me-0 pe-0">
                <i class="nav-link fas fa-book fa-fw fa-fw align-self-center me-3 active"></i>
                <a class="nav-link flex-fill align-self-center me-auto active" href="{reverse('ledger:ledger_index')}">
                    Ledger
                </a>
            </li>
        """

    def test_menu_hook(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("ledger:ledger_index"))

        self.assertContains(response, self.html_menu, html=True)

    def test_render_returns_empty_string_for_user_without_permission(self):
        # given
        ledger_menu_item = LedgerMenuItem()
        mock_request = MagicMock()
        mock_request.user.has_perm.return_value = False

        # when
        result = ledger_menu_item.render(mock_request)
        # then
        self.assertEqual(
            result,
            "",
            "Expected render method to return an empty string for users without permission",
        )

    def test_register_charlink_hook(self):
        # Verify that the hook returns the expected value
        result = register_charlink_hook()
        self.assertEqual(result, "ledger.thirdparty.charlink_hook")
