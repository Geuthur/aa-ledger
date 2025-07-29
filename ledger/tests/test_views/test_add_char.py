"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

# AA Ledger
from ledger.models.characteraudit import CharacterAudit
from ledger.tests.testdata.generate_characteraudit import (
    create_user_from_evecharacter_with_access,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse
from ledger.views.character.add_char import add_char

MODULE_PATH = "ledger.views.character.add_char"


@patch(MODULE_PATH + ".messages")
@patch(MODULE_PATH + ".tasks")
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestAddCharView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )

    def _add_character(self, user, token):
        request = self.factory.get(reverse("ledger:add_char"))
        request.user = user
        request.token = token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        orig_view = add_char.__wrapped__.__wrapped__.__wrapped__
        return orig_view(request, token)

    def test_add_char(self, mock_tasks, mock_messages):
        # given
        user = self.user
        token = user.token_set.get(character_id=1001)
        # when
        response = self._add_character(user, token)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("ledger:character_ledger", args=[1001]))
        self.assertTrue(mock_tasks.update_character.apply_async.called)
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(
            CharacterAudit.objects.filter(eve_character__character_id=1001).exists()
        )
