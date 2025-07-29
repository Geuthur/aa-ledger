"""TestView class."""

# Standard Library
import json
from http import HTTPStatus

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse

# AA Ledger
from ledger.tests.testdata.generate_characteraudit import (
    add_characteraudit_character_to_user,
    create_user_from_evecharacter_with_access,
)

# AA Skillfarm
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse
from ledger.views.character.character_ledger import character_delete

MODULE_PATH = "ledger.views.character.character_ledger"


class TestDeleteCharacterView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )
        cls.audit = add_characteraudit_character_to_user(cls.user, 1001)
        cls.no_audit_user, cls.character_ownership = (
            create_user_from_evecharacter_with_access(1002)
        )

    def test_delete_character(self):
        character_id = self.audit.eve_character.character_id

        request = self.factory.post(reverse("ledger:delete_char", args=[character_id]))
        request.user = self.user

        response = character_delete(request, character_id=character_id)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "Gneuten successfully deleted")

    def test_delete_character_no_permission(self):
        request = self.factory.post(reverse("ledger:delete_char", args=[1001]))
        request.user = self.no_audit_user

        response = character_delete(request, character_id=1001)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")
