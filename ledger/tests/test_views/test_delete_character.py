"""TestView class."""

# Standard Library
import json
from http import HTTPStatus

# Django
from django.urls import reverse

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import (
    create_owner_from_user,
)
from ledger.views.character.character_ledger import character_delete

MODULE_PATH = "ledger.views.character.character_ledger"


class TestDeleteCharacterView(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(cls.user, owner_type="character")

    def test_delete_character(self):
        """
        Test deleting a character that the user has permission to delete.

        This test verifies that when a user with the appropriate permissions
        attempts to delete a character they own, the system successfully deletes
        the character and provides appropriate feedback.

        ## Results: Character is deleted successfully.
        """
        character_id = self.audit.eve_character.character_id

        request = self.factory.post(reverse("ledger:delete_char", args=[character_id]))
        request.user = self.user

        response = character_delete(request, character_id=character_id)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "Gneuten successfully deleted")

    def test_delete_character_no_permission(self):
        """
        Test deleting a character that the user does not have permission to delete.

        This test verifies that when a user without the appropriate permissions
        attempts to delete a character they do not own, the system prevents the
        deletion and provides an appropriate error message.

        ## Results: Permission Denied error is returned.
        """
        request = self.factory.post(reverse("ledger:delete_char", args=[1001]))
        request.user = self.user2

        response = character_delete(request, character_id=1001)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")
