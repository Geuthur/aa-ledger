# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse

# Alliance Auth (External Libs)
from evesde_factory.utils import add_permission_to_user

# AA Ledger
from ledger.models import CharacterOwner, CorporationOwner
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import CharacterOwnerFactory, CorporationOwnerFactory


class TestAdministrationApi(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = f"{reverse('ledger:index')}api"

    def test_character_administration_should_list_registered_characters(self):
        # Test Data
        owner = CharacterOwnerFactory(user=self.user)
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(
            f"{self.api}/character/{owner.eve_id}/administration/"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(
            [row["owner_id"] for row in data["registered"]], [owner.eve_id]
        )
        self.assertEqual(data["dashboard"]["active_count"], 1)
        self.assertEqual(data["owner"]["character_id"], owner.eve_id)

    def test_character_administration_should_return_404_for_unknown_character(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.api}/character/1/administration/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_corporation_administration_should_return_403_without_permission(self):
        # Test Data
        audit = CorporationOwnerFactory(user=self.manage_user)
        self.client.force_login(self.user2)

        # Test Action
        response = self.client.get(
            f"{self.api}/corporation/{audit.eve_id}/administration/"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_corporation_administration_should_list_the_corporation(self):
        # Test Data
        audit = CorporationOwnerFactory(user=self.manage_user)
        self.client.force_login(self.manage_user)

        # Test Action
        response = self.client.get(
            f"{self.api}/corporation/{audit.eve_id}/administration/"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(
            [row["owner_id"] for row in data["registered"]], [audit.eve_id]
        )
        self.assertEqual(
            data["dashboard"]["missing_count"],
            data["dashboard"]["auth_count"] - data["dashboard"]["active_count"],
        )

    def test_alliance_administration_should_count_corporations(self):
        # Test Data
        audit = CorporationOwnerFactory(user=self.manage_user)
        self.client.force_login(self.manage_user)
        alliance_id = audit.eve_corporation.alliance.alliance_id

        # Test Action
        response = self.client.get(f"{self.api}/alliance/{alliance_id}/administration/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json()["dashboard"]["active_count"], 1)
        self.assertEqual(len(response.json()["registered"]), 1)


class TestDeleteApi(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = f"{reverse('ledger:index')}api"

    def test_delete_character_should_remove_the_character(self):
        # Test Data
        owner = CharacterOwnerFactory(user=self.user)
        self.client.force_login(self.user)

        # Test Action
        response = self.client.delete(f"{self.api}/character/{owner.eve_id}/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response.json()["message"],
            f"{self.user_character.character_name} successfully deleted",
        )
        self.assertFalse(CharacterOwner.objects.filter(pk=owner.pk).exists())

    def test_delete_character_should_return_403_without_permission(self):
        # Test Data
        owner = CharacterOwnerFactory(user=self.user)
        self.client.force_login(self.user2)

        # Test Action
        response = self.client.delete(f"{self.api}/character/{owner.eve_id}/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTrue(CharacterOwner.objects.filter(pk=owner.pk).exists())

    def test_delete_corporation_should_remove_the_corporation(self):
        # Test Data
        audit = CorporationOwnerFactory(user=self.manage_own_user)
        self.client.force_login(self.manage_own_user)

        # Test Action
        response = self.client.delete(f"{self.api}/corporation/{audit.eve_id}/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(CorporationOwner.objects.filter(pk=audit.pk).exists())

    def test_delete_corporation_should_return_404_for_unknown_corporation(self):
        # Test Data
        self.client.force_login(self.manage_user)

        # Test Action
        response = self.client.delete(f"{self.api}/corporation/2002/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_delete_corporation_should_return_403_for_foreign_corporation(self):
        # Test Data
        audit = CorporationOwnerFactory(user=self.manage_own_user)
        add_permission_to_user(user=self.user2, permissions=["ledger.manage_access"])
        self.client.force_login(self.user2)

        # Test Action
        response = self.client.delete(f"{self.api}/corporation/{audit.eve_id}/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTrue(CorporationOwner.objects.filter(pk=audit.pk).exists())
