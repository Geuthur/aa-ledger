"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.test import override_settings
from django.urls import reverse

# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo
from allianceauth.eveonline.providers import Alliance, ObjectNotFound

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import (
    add_new_permission_to_user,
)

MODULE_PATH = "ledger.views.alliance.add_ally"


@patch(MODULE_PATH + ".messages")
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestAddAllyView(LedgerTestCase):
    """Test Add Ally View."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alliance = Alliance(
            id=3005,
            name="Test Alliance",
            ticker="T.E.S.T",
            corp_ids=[2001, 2002],
            executor_corp_id=None,
            faction_id=None,
        )

    def test_add_ally_already_exist(self, mock_messages):
        """
        Test adding an ally that already exists in the system.

        This test ensures that when an ally that already exists in the system is
        added again, the system correctly identifies it and provides appropriate
        feedback to the user without attempting to create a duplicate entry.

        ## Results: Redirects to alliance ledger with info message.
        """
        # Test Data
        self.user = add_new_permission_to_user(self.user, "ledger.advanced_access")
        token = self.user.token_set.get(character_id=1001)

        # Test Action
        response = self._add_alliance(self.user, token)

        # Expected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("ledger:alliance_overview"))
        self.assertEqual(mock_messages.info.call_count, 1)

    @patch(MODULE_PATH + ".provider")
    @patch(MODULE_PATH + ".EveAllianceInfo.objects.get_or_create")
    @patch(MODULE_PATH + ".EveAllianceInfo.objects.get")
    def test_add_ally_does_not_exist(
        self, mock_get, mock_get_or_create, mock_provider, mock_messages
    ):
        """
        Test adding an ally that does not exist in the system.

        This test verifies that when an ally that does not exist in the system is
        added, the system successfully creates a new entry and provides appropriate
        feedback to the user.

        ## Results: Ally is added successfully.
        """
        # Test Data
        self.user = add_new_permission_to_user(self.user, "ledger.advanced_access")
        mock_get.side_effect = EveAllianceInfo.DoesNotExist
        mock_provider.get_alliance.return_value = self.alliance

        mock_ally = Mock()
        mock_ally.populate_alliance = Mock()
        mock_ally.alliance_id = 3005
        mock_ally.alliance_name = "Test Alliance"
        mock_ally.alliance_ticker = "T.E.S.T"
        mock_ally.executor_corp_id = 2001
        mock_get_or_create.return_value = (mock_ally, True)
        token = self.user.token_set.get(character_id=1001)

        # Test Action
        response = self._add_alliance(self.user, token)

        # Expected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("ledger:alliance_overview"))
        self.assertEqual(mock_messages.success.call_count, 1)
        mock_get.assert_called_once_with(alliance_id=3001)
        mock_provider.get_alliance.assert_called_once_with(3001)
        mock_get_or_create.assert_called_once()

    @patch(MODULE_PATH + ".provider")
    @patch(MODULE_PATH + ".EveAllianceInfo.objects.get_or_create")
    @patch(MODULE_PATH + ".EveAllianceInfo.objects.get")
    def test_add_ally_does_not_exist_object_not_found(
        self, mock_get, mock_get_or_create, mock_provider, mock_messages
    ):
        """
        Test adding an ally that does not exist and is not found by the provider.

        This test ensures that when an ally that does not exist in the system is
        attempted to be added but is not found by the external provider, the system

        ## Results: Redirects to alliance ledger with warning message.
        """
        # Test Data
        self.user = add_new_permission_to_user(self.user, "ledger.advanced_access")
        mock_get.side_effect = EveAllianceInfo.DoesNotExist
        mock_provider.get_alliance.side_effect = ObjectNotFound(3001, "alliance")

        token = self.user.token_set.get(character_id=1001)

        # Test Action
        response = self._add_alliance(self.user, token)

        # Expected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("ledger:alliance_overview"))
        self.assertEqual(mock_messages.warning.call_count, 1)
        mock_get_or_create.assert_not_called()
