"""TestView class."""

# Standard Library
import json
from http import HTTPStatus

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import (
    add_new_permission_to_user,
    create_owner_from_user,
)
from ledger.views.corporation.corporation_ledger import corporation_delete

MODULE_PATH = "ledger.views.corporation.corporation_ledger"


class TestDeleteCorporationView(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(
            user=cls.user,
            owner_type="corporation",
        )

    def test_delete_corporation(self):
        """
        Test deleting a corporation successfully.

        This test verifies that a user with the appropriate permissions can successfully
        delete a corporation from the system. It checks that the response indicates success
        and that the correct success message is returned.

        ## Results: Corporation is deleted successfully.
        """
        # Test Data
        request = self.factory.post(
            reverse(
                "ledger:delete_corp",
                kwargs={"corporation_id": self.audit.eve_corporation.corporation_id},
            )
        )
        request.user = self.manage_own_user

        # Test Action
        response = corporation_delete(
            request, corporation_id=self.audit.eve_corporation.corporation_id
        )

        # Expected Results
        response_data = json.loads(response.content)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "Hell RiderZ successfully deleted")

    def test_delete_corporation_no_audit(self):
        """
        Test deleting a corporation that does not exist.

        This test verifies that when a user attempts to delete a corporation that does not
        exist in the system, the appropriate error response is returned.

        ## Results: Corporation not found message is returned.
        """
        # Test Data
        request = self.factory.post(
            reverse("ledger:delete_corp", kwargs={"corporation_id": 2002})
        )
        request.user = self.manage_user

        # Test Action
        response = corporation_delete(request, corporation_id=2002)

        # Expected Results
        response_data = json.loads(response.content)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Corporation not found")

    def test_delete_corporation_no_permission(self):
        """
        Test deleting a corporation without being in the corporation.

        This test verifies that when a user without the necessary permissions
        attempts to delete a corporation, the system prevents the deletion and
        provides an appropriate error message.

        ## Results: Permission Denied message is returned.
        """
        # Test Data
        request = self.factory.post(
            reverse(
                "ledger:delete_corp",
                kwargs={"corporation_id": self.audit.eve_corporation.corporation_id},
            )
        )
        add_new_permission_to_user(
            user=self.user2, permission_name="ledger.manage_access"
        )
        request.user = self.user2

        # Test Action
        response = corporation_delete(
            request, corporation_id=self.audit.eve_corporation.corporation_id
        )
        # Expected Results
        response_data = json.loads(response.content)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")
