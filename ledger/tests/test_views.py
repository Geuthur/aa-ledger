from http import HTTPStatus

from django.test import RequestFactory, TestCase
from django.urls import reverse

from ledger.views.pve import ledger_index


class TestViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()

    def test_view(self):
        request = self.factory.get(reverse("ledger:index"))
        request.user = self.user
        response = ledger_index(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.url, reverse("ledger:ledger_char_index"))
