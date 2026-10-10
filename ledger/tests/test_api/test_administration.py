# Standard Library
from datetime import timedelta
from http import HTTPStatus
from unittest.mock import patch

# Django
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone

# Alliance Auth (External Libs)
from evesde_factory.utils import add_permission_to_user

# AA Ledger
from ledger.app_settings import LEDGER_MANUAL_UPDATE_COOLDOWN
from ledger.models import CharacterOwner, CorporationOwner
from ledger.models.helpers.update_manager import (
    CharacterUpdateSection,
    CorporationUpdateSection,
)
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CharacterOwnerFactory,
    CharacterUpdateStatusFactory,
    CorporationOwnerFactory,
    CorporationUpdateStatusFactory,
)


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

    def test_character_administration_should_include_last_sync_and_cooldown_fields(
        self,
    ):
        # Test Data
        owner = CharacterOwnerFactory(user=self.user)
        sync_time = timezone.now() - timedelta(minutes=10)
        CharacterUpdateStatusFactory(
            owner=owner,
            section=CharacterUpdateSection.WALLET_JOURNAL,
            last_run_finished_at=sync_time,
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(
            f"{self.api}/character/{owner.eve_id}/administration/"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertIsNotNone(data["last_sync"])
        self.assertTrue(data["can_update"])
        self.assertEqual(data["cooldown_seconds"], 0)
        self.assertEqual(len(data["registered"]), 1)
        self.assertIsNotNone(data["registered"][0]["last_sync"])

    def test_character_administration_should_show_cooldown_when_recently_updated(self):
        # Test Data
        owner = CharacterOwnerFactory(user=self.user)
        sync_time = timezone.now() - timedelta(seconds=60)
        CharacterUpdateStatusFactory(
            owner=owner,
            section=CharacterUpdateSection.WALLET_JOURNAL,
            last_run_finished_at=sync_time,
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(
            f"{self.api}/character/{owner.eve_id}/administration/"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertFalse(data["can_update"])
        self.assertGreater(data["cooldown_seconds"], 0)
        self.assertLessEqual(data["cooldown_seconds"], LEDGER_MANUAL_UPDATE_COOLDOWN)

    @patch("ledger.api.administration.update_user_characters.apply_async")
    def test_trigger_character_update_should_queue_task_and_set_cooldown(
        self, mock_apply_async
    ):
        # Test Data
        owner = CharacterOwnerFactory(user=self.user)
        cache_key = f"aa_ledger_user_update_cooldown_{self.user.id}"
        cache.delete(cache_key)
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(f"{self.api}/character/{owner.eve_id}/update/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_apply_async.assert_called_once_with(
            args=[self.user.id], kwargs={"force_refresh": True}
        )
        self.assertIsNotNone(cache.get(cache_key))
        cache.delete(cache_key)

    def test_trigger_character_update_should_return_429_on_cooldown(self):
        # Test Data
        owner = CharacterOwnerFactory(user=self.user)
        cache_key = f"aa_ledger_user_update_cooldown_{self.user.id}"
        cache.set(cache_key, timezone.now() + timedelta(seconds=200), timeout=200)
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(f"{self.api}/character/{owner.eve_id}/update/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.TOO_MANY_REQUESTS)
        self.assertIn("error", response.json())
        cache.delete(cache_key)

    def test_trigger_character_update_should_return_404_for_unknown_character(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(f"{self.api}/character/999999/update/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_trigger_character_update_should_return_403_without_permission(self):
        # Test Data
        owner = CharacterOwnerFactory(user=self.user)
        self.client.force_login(self.user2)

        # Test Action
        response = self.client.post(f"{self.api}/character/{owner.eve_id}/update/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

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
        # manage_user's main character is in the corporation but not registered as CharacterOwner
        self.assertEqual(len(data["missing"]), 1)
        self.assertEqual(
            data["missing"][0]["owner_id"],
            self.manage_user.profile.main_character.character_id,
        )
        self.assertFalse(data["members"][0]["is_registered"])

        # When character is registered in CharacterOwner
        CharacterOwnerFactory(eve_character=self.manage_user.profile.main_character)
        response_registered = self.client.get(
            f"{self.api}/corporation/{audit.eve_id}/administration/"
        )
        data_reg = response_registered.json()
        self.assertEqual(len(data_reg["missing"]), 0)
        self.assertTrue(data_reg["members"][0]["is_registered"])

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
        self.assertIsNone(response.json()["last_sync"])

    def test_alliance_administration_should_include_corporation_last_sync(self):
        # Test Data
        audit = CorporationOwnerFactory(user=self.manage_user)
        sync_time = timezone.now() - timedelta(minutes=15)
        CorporationUpdateStatusFactory(
            owner=audit,
            section=CorporationUpdateSection.WALLET_JOURNAL,
            last_run_finished_at=sync_time,
        )
        self.client.force_login(self.manage_user)
        alliance_id = audit.eve_corporation.alliance.alliance_id

        # Test Action
        response = self.client.get(f"{self.api}/alliance/{alliance_id}/administration/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertIsNone(data["last_sync"])
        self.assertIsNotNone(data["registered"][0]["last_sync"])


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
