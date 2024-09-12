from http import HTTPStatus

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase
from django.urls import reverse

from app_utils.testdata_factories import UserMainFactory

from ledger.models.general import General
from ledger.views.alliance.alliance_ledger import alliance_admin, alliance_ledger
from ledger.views.character.character_ledger import character_admin, character_ledger
from ledger.views.character.planetary import planetary_admin
from ledger.views.corporation.corporation_ledger import (
    corporation_admin,
    corporation_ledger,
)
from ledger.views.pve import ledger_index


class TestViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        cls.user = UserMainFactory(
            permissions=[
                "ledger.basic_access",
                "ledger.advanced_access",
            ]
        )

    def test_view(self):
        request = self.factory.get(reverse("ledger:index"))
        request.user = self.user
        response = ledger_index(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_char_ledger_view(self):
        request = self.factory.get(
            reverse("ledger:character_ledger", kwargs={"character_pk": 0})
        )
        request.user = self.user
        response = character_ledger(request, character_pk=0)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_char_ledger_admin_view(self):
        request = self.factory.get(reverse("ledger:character_admin"))
        request.user = self.user
        response = character_admin(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_corp_ledger_view(self):
        request = self.factory.get(
            reverse("ledger:corporation_ledger", kwargs={"corporation_pk": 0})
        )
        request.user = self.user
        response = corporation_ledger(request, corporation_pk=0)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_corp_ledger_admin_view(self):
        request = self.factory.get(reverse("ledger:corporation_admin"))
        request.user = self.user
        response = corporation_admin(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_char_ledger_planetary_admin_view(self):
        request = self.factory.get(reverse("ledger:planetary_admin"))
        request.user = self.user
        response = planetary_admin(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_ally_ledger_view(self):
        request = self.factory.get(
            reverse("ledger:alliance_ledger", kwargs={"alliance_pk": 0})
        )
        request.user = self.user
        response = alliance_ledger(request, alliance_pk=0)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_ally_ledger_admin_view(self):
        request = self.factory.get(reverse("ledger:alliance_admin"))
        request.user = self.user
        response = alliance_admin(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
