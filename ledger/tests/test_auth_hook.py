# Standard Library
from unittest.mock import MagicMock

# Django
from django.urls import reverse

# AA Ledger
from ledger.auth_hooks import LedgerMenuItem, register_charlink_hook
from ledger.tests import LedgerTestCase


class TestAuthHooks(LedgerTestCase):
    """Test Alliance Auth Menu Hooks for Ledger"""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.html_menu = f"""
            <li class="d-flex flex-wrap m-2 p-2 pt-0 pb-0 mt-0 mb-0 me-0 pe-0">
                <i class="nav-link fas fa-book fa-fw fa-fw align-self-center me-3 active"></i>
                <a class="nav-link flex-fill align-self-center me-auto active" href="{reverse('ledger:index')}">
                    Ledger
                </a>
            </li>
        """

    def test_menu_hook(self):
        """
        Test that the menu hook renders correctly for a user with permission.

        This test logs in a user with the 'ledger.basic_access' permission
        and verifies that the Ledger menu item is present in the rendered HTML.
        """
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(
            reverse("ledger:index"), follow=True
        )  # Follow redirects

        # Expected Results
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.html_menu, html=True)

    def test_render_returns_empty_string_for_user_without_permission(self):
        """
        Test that the render method returns an empty string for a user without permission.

        This test creates a mock request for a user who lacks the 'ledger.basic_access' permission
        and verifies that the render method of LedgerMenuItem returns an empty string.
        """
        # Test Data
        ledger_menu_item = LedgerMenuItem()
        mock_request = MagicMock()
        mock_request.user.has_perm.return_value = False

        # Test Action
        result = ledger_menu_item.render(mock_request)

        # Expected Result
        self.assertEqual(
            result,
            "",
            "Expected render method to return an empty string for users without permission",
        )

    def test_register_charlink_hook(self):
        """
        Test that the register_charlink_hook function returns the expected value.

        This test calls the register_charlink_hook function and verifies that it returns
        the correct string indicating the charlink hook location.
        """
        # Test Action
        result = register_charlink_hook()

        # Expected Result
        self.assertEqual(result, "ledger.thirdparty.charlink_hook")
