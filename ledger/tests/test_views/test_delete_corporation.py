"""TestView class."""

# Standard Library
import json
from http import HTTPStatus

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse

# AA Ledger
from ledger.tests.testdata.generate_corporationaudit import (
    add_corporationaudit_corporation_to_user,
    create_user_from_evecharacter,
)

# AA Skillfarm
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse
from ledger.views.corporation.corporation_ledger import corporation_delete

MODULE_PATH = "ledger.views.corporation.corporation_ledger"


class TestDeleteCorporationView(TestCase):
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
                "ledger.corp_audit_manager",
                "ledger.manage_access",
            ],
        )
        cls.audit = add_corporationaudit_corporation_to_user(cls.user, 1001)
        cls.no_audit_user, cls.character_ownership = create_user_from_evecharacter(
            1002,
            permissions=[
                "ledger.basic_access",
                "ledger.advanced_access",
                "ledger.manage_access",
            ],
        )

    def test_delete_corporation(self):
        corporation_id = self.audit.corporation.corporation_id

        request = self.factory.post(
            reverse("ledger:delete_corp", args=[corporation_id])
        )
        request.user = self.user

        response = corporation_delete(request, corporation_id=corporation_id)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "Hell RiderZ successfully deleted")

    def test_delete_corporation_no_audit(self):
        request = self.factory.post(reverse("ledger:delete_corp", args=[2002]))
        request.user = self.user

        response = corporation_delete(request, corporation_id=2002)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Corporation not found")

    def test_delete_corporation_no_permission(self):
        """Test deleting a corporation without being in the corporation."""
        request = self.factory.post(reverse("ledger:delete_corp", args=[2001]))
        request.user = self.no_audit_user

        response = corporation_delete(request, corporation_id=2001)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")
