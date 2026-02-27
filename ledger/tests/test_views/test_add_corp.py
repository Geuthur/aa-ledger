"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Django
from django.test import override_settings
from django.urls import reverse

# AA Ledger
from ledger.models.corporationaudit import CorporationOwner
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import add_new_permission_to_user

MODULE_PATH = "ledger.views.corporation.add_corp"


@patch(MODULE_PATH + ".messages")
@patch(MODULE_PATH + ".tasks")
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestAddCorpView(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_add_corp(self, mock_tasks, mock_messages):
        """Test adding a corporation via the add_corp view."""
        # Test Data
        self.user = add_new_permission_to_user(self.user, "ledger.advanced_access")
        user = self.user
        token = user.token_set.get(character_id=1001)

        # Test Action
        response = self._add_corporation(user, token)

        # Expected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("ledger:corporation_overview"))
        self.assertTrue(mock_tasks.update_corporation.apply_async.called)
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(
            CorporationOwner.objects.filter(
                eve_corporation__corporation_id=2001
            ).exists()
        )
