from http import HTTPStatus

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase
from django.urls import reverse

from app_utils.testdata_factories import UserMainFactory

from ledger.models import General
from ledger.views.pve import ledger_index, ratting_char_index


class TestViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        cls.user = UserMainFactory()

        content_type = ContentType.objects.get_for_model(General)
        permission = Permission.objects.create(
            codename="basic_access",
            name="Can access basic features",
            content_type=content_type,
        )
        cls.user.user_permissions.add(permission)

    def test_view(self):
        request = self.factory.get(reverse("ledger:index"))
        request.user = self.user
        response = ledger_index(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_ledger_view(self):
        request = self.factory.get(reverse("ledger:ledger_char_index"))
        request.user = self.user
        response = ratting_char_index(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
