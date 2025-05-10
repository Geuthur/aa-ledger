"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

# AA Ledger
from ledger.models.corporationaudit import CorporationAudit
from ledger.tests.testdata.generate_corporationaudit import (
    create_user_from_evecharacter,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse
from ledger.views.corporation.add_corp import add_corp

MODULE_PATH = "ledger.views.corporation.add_corp"


@patch(MODULE_PATH + ".messages")
@patch(MODULE_PATH + ".tasks")
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestAddCorpView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
                "ledger.advanced_access",
            ],
        )

    def _add_corporation(self, user, token):
        request = self.factory.get(reverse("ledger:add_corp"))
        request.user = user
        request.token = token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        orig_view = add_corp.__wrapped__.__wrapped__.__wrapped__
        return orig_view(request, token)

    def test_add_corp(self, mock_tasks, mock_messages):
        # given
        user = self.user
        token = user.token_set.get(character_id=1001)
        # when
        response = self._add_corporation(user, token)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            response.url, reverse("ledger:corporation_ledger", args=[2001])
        )
        self.assertTrue(mock_tasks.update_corporation.apply_async.called)
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(
            CorporationAudit.objects.filter(corporation__corporation_id=2001).exists()
        )
