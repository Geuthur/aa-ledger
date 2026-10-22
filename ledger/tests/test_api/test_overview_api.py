# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CharacterOwnerFactory,
    CharacterUpdateStatusFactory,
    CorporationOwnerFactory,
)


class TestOverviewApi(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = f"{reverse('ledger:index')}api"

    def test_get_overview_should_return_403_without_basic_access(self):
        # Test Data
        user = self.user
        user.user_permissions.clear()
        self.client.force_login(user)

        # Test Action
        response = self.client.get(f"{self.api}/overview/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_overview_should_return_character_visible_to_user(self):
        # Test Data
        self.client.force_login(self.user)
        CharacterOwnerFactory(
            eve_character=self.user_character,
            character_name=self.user_character.character_name,
        )

        # Test Action
        response = self.client.get(f"{self.api}/overview/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertIn("owners", data)
        owner_ids = [o["id"] for o in data["owners"]]
        self.assertIn(self.user_character.character_id, owner_ids)

    def test_get_overview_should_return_all_owners_for_superuser(self):
        # Test Data
        self.client.force_login(self.superuser)
        char_owner = CharacterOwnerFactory()
        corp_owner = CorporationOwnerFactory()

        # Test Action
        response = self.client.get(f"{self.api}/overview/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        owner_ids = [o["id"] for o in data["owners"]]
        self.assertIn(char_owner.eve_character.character_id, owner_ids)
        self.assertIn(corp_owner.eve_corporation.corporation_id, owner_ids)

    def test_get_overview_should_flag_owner_with_errors(self):
        # Test Data
        self.client.force_login(self.user)
        char_owner = CharacterOwnerFactory(
            eve_character=self.user_character,
            character_name=self.user_character.character_name,
        )
        CharacterUpdateStatusFactory(
            owner=char_owner,
            is_success=False,
            error_message="Token Expired",
        )

        # Test Action
        response = self.client.get(f"{self.api}/overview/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        owner = next(
            o for o in data["owners"] if o["id"] == self.user_character.character_id
        )
        self.assertTrue(owner["has_errors"])
