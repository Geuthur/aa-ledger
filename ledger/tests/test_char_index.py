from unittest.mock import Mock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse

from app_utils.testdata_factories import UserMainFactory

from ledger.views.character.char_audit import add_char, fetch_memberaudit


class AddCharTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(
            permissions=[
                "ledger.basic_access",
            ]
        )

    def test_add_char(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("ledger:add_char"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ledger/index.html")


class FetchMemberAuditTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(
            permissions=[
                "ledger.basic_access",
            ]
        )

    def test_fetch_memberaudit(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("ledger:ledger_fetch_memberaudit"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ledger/index.html")
