"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Django
from django.urls import reverse

# AA Ledger
from ledger.models.characteraudit import CharacterOwner
from ledger.tests import AuthTestCase
from ledger.tests.testdata.view_helpers import add_character

MODULE_PATH = "ledger.views"


@patch(MODULE_PATH + ".messages")
@patch(MODULE_PATH + ".tasks")
class TestAddCharView(AuthTestCase):
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
        response = add_character(self.factory, self.user, token)

        # Expected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("ledger:index"))
        self.assertTrue(mock_tasks.update_character.apply_async.called)
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(
            CharacterOwner.objects.filter(
                eve_character__character_id=self.user.profile.main_character.character_id
            ).exists()
        )
