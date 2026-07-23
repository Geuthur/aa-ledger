"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Django
from django.urls import reverse

# AA Ledger
from ledger.models.characteraudit import CharacterOwner
from ledger.tests import LedgerTestCase

MODULE_PATH = "ledger.views.character.add_char"


@patch(MODULE_PATH + ".messages")
@patch(MODULE_PATH + ".tasks")
class TestAddCharView(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_add_char(self, mock_tasks, mock_messages):
        """
        Test adding a character that does not exist in the system.

        This test verifies that when a character that does not exist in the system is
        added, the system successfully creates a new entry and provides appropriate
        feedback to the user.

        ## Results: Character is added successfully.
        """
        # Test Data
        token = self.user.token_set.first()

        # Test Action
        response = self._add_character(self.user, token)

        # Expected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("ledger:index"))
        self.assertTrue(mock_tasks.update_character.apply_async.called)
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(
            CharacterOwner.objects.filter(
                eve_character__character_id=self.user_character.character_id
            ).exists()
        )
