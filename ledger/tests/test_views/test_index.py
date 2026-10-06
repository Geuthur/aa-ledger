# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse

# AA Ledger
from ledger.tests import LedgerTestCase


class TestReactBaseView(LedgerTestCase):
    def test_should_serve_the_react_shell_for_frontend_routes(self):
        # Test Data
        self.client.force_login(self.user)
        urls = [
            reverse("ledger:index"),
            "/ledger/character/90000001/?year=2026",
            "/ledger/corporation/",
            "/ledger/settings/",
        ]

        for url in urls:
            with self.subTest(url=url):
                # Test Action
                response = self.client.get(url)

                # Expected Result
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertContains(response, 'id="aa-ledger-root"')

    def test_should_not_serve_the_shell_for_api_routes(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get("/ledger/api/unknown/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_should_require_basic_access(self):
        # Test Data
        self.client.force_login(self.user)
        self.user.user_permissions.clear()

        # Test Action
        response = self.client.get(reverse("ledger:index"))

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
