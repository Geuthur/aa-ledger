# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Django
from django.urls import reverse

# Alliance Auth (External Libs)
from evesde_factory.allianceauth import (
    EveAllianceInfoFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
)
from evesde_factory.utils import add_character_to_user

# AA Ledger
from ledger.models.characteraudit import CharacterOwner
from ledger.models.corporationaudit import CorporationOwner
from ledger.models.general import General
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CharacterOwnerFactory,
    CorporationOwnerFactory,
    UserMainFactory,
)


class TestSuperuserApi(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = f"{reverse('ledger:index')}api"

    def test_get_superuser_owners_should_return_403_for_regular_user(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.api}/superuser/owners/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_superuser_owners_should_return_all_owners_for_superuser(self):
        # Test Data
        self.client.force_login(self.superuser)
        char_owner = CharacterOwnerFactory()
        corp_owner = CorporationOwnerFactory()

        # Test Action
        response = self.client.get(f"{self.api}/superuser/owners/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        owner_ids = [item["owner_id"] for item in data]
        self.assertIn(char_owner.eve_character.character_id, owner_ids)
        self.assertIn(corp_owner.eve_corporation.corporation_id, owner_ids)

    def test_get_superuser_owners_should_only_return_main_character(self):
        # Test Data
        self.client.force_login(self.superuser)
        user = UserMainFactory()
        main_owner = CharacterOwnerFactory(user=user)
        alt_char = EveCharacterFactory()
        add_character_to_user(user=user, character=alt_char, is_main=False)
        CharacterOwnerFactory(user=user, eve_character=alt_char)

        # Test Action
        response = self.client.get(f"{self.api}/superuser/owners/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        owner_ids = [item["owner_id"] for item in data]
        self.assertIn(main_owner.eve_character.character_id, owner_ids)
        self.assertNotIn(alt_char.character_id, owner_ids)

    @patch("ledger.api.superuser.tasks.update_character.apply_async")
    def test_trigger_update_character_should_queue_task(self, mock_task):
        # Test Data
        self.client.force_login(self.superuser)
        char_owner = CharacterOwnerFactory()

        # Test Action
        response = self.client.post(
            f"{self.api}/superuser/owners/character/{char_owner.eve_character.character_id}/update/",
            data={"force_refresh": True},
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(mock_task.called)

    @patch("ledger.api.superuser.tasks.update_corporation.apply_async")
    def test_trigger_update_corporation_should_queue_task(self, mock_task):
        # Test Data
        self.client.force_login(self.superuser)
        corp_owner = CorporationOwnerFactory()

        # Test Action
        response = self.client.post(
            f"{self.api}/superuser/owners/corporation/{corp_owner.eve_corporation.corporation_id}/update/",
            data={"force_refresh": False},
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(mock_task.called)

    def test_trigger_update_should_return_404_if_not_found(self):
        # Test Data
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(
            f"{self.api}/superuser/owners/character/99999999/update/",
            data={"force_refresh": False},
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_delete_character_owner_should_remove_owner(self):
        # Test Data
        self.client.force_login(self.superuser)
        char_owner = CharacterOwnerFactory()
        char_id = char_owner.eve_character.character_id

        # Test Action
        response = self.client.delete(
            f"{self.api}/superuser/owners/character/{char_id}/"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(
            CharacterOwner.objects.filter(eve_character__character_id=char_id).exists()
        )

    def test_delete_corporation_owner_should_remove_owner(self):
        # Test Data
        self.client.force_login(self.superuser)
        corp_owner = CorporationOwnerFactory()
        corp_id = corp_owner.eve_corporation.corporation_id

        # Test Action
        response = self.client.delete(
            f"{self.api}/superuser/owners/corporation/{corp_id}/"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(
            CorporationOwner.objects.filter(
                eve_corporation__corporation_id=corp_id
            ).exists()
        )

    def test_inspect_character_owner_should_return_administration_data(self):
        # Test Data
        self.client.force_login(self.superuser)
        char_owner = CharacterOwnerFactory()
        char_id = char_owner.eve_character.character_id

        # Test Action
        response = self.client.get(
            f"{self.api}/superuser/owners/character/{char_id}/inspect/"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertIn("dashboard", data)
        self.assertIn("registered", data)
        self.assertEqual(data["owner"]["character_id"], char_id)

    def test_inspect_corporation_owner_should_return_administration_data(self):
        # Test Data
        self.client.force_login(self.superuser)
        corp_owner = CorporationOwnerFactory()
        corp_id = corp_owner.eve_corporation.corporation_id

        # Test Action
        response = self.client.get(
            f"{self.api}/superuser/owners/corporation/{corp_id}/inspect/"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertIn("dashboard", data)
        self.assertIn("registered", data)
        self.assertEqual(data["owner"]["character_id"], corp_id)

    def test_get_superuser_owners_should_return_only_own_corporations_for_corp_audit_manager(
        self,
    ):
        # Test Data
        self.client.force_login(self.manage_own_user)
        own_corp = CorporationOwnerFactory(user=self.manage_own_user)
        other_corp = CorporationOwnerFactory()

        # Test Action
        response = self.client.get(f"{self.api}/superuser/owners/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        owner_ids = [item["owner_id"] for item in data]
        self.assertIn(own_corp.eve_corporation.corporation_id, owner_ids)
        self.assertNotIn(other_corp.eve_corporation.corporation_id, owner_ids)

    def test_get_superuser_owners_should_return_only_own_corp_characters_for_char_audit_manager(
        self,
    ):
        # Test Data
        char_manager_user = UserMainFactory(
            permissions__=[General.get_perm(General.Permission.CHAR_AUDIT_MANAGER)]
        )
        char_manager = char_manager_user.profile.main_character
        char_in_corp = EveCharacterFactory(corporation_id=char_manager.corporation_id)
        user_in_corp = UserMainFactory()
        add_character_to_user(user=user_in_corp, character=char_in_corp, is_main=True)
        owner_in_corp = CharacterOwnerFactory(eve_character=char_in_corp)

        char_other_corp = EveCharacterFactory(corporation_id=888888)
        user_other = UserMainFactory()
        add_character_to_user(user=user_other, character=char_other_corp, is_main=True)
        CharacterOwnerFactory(eve_character=char_other_corp)

        self.client.force_login(char_manager_user)

        # Test Action
        response = self.client.get(f"{self.api}/superuser/owners/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        owner_ids = [item["owner_id"] for item in response.json()]
        self.assertIn(owner_in_corp.eve_character.character_id, owner_ids)
        self.assertNotIn(char_other_corp.character_id, owner_ids)

    def test_delete_corporation_owner_should_return_403_for_non_admin_manager(
        self,
    ):
        # Test Data
        self.client.force_login(self.manage_own_user)
        own_corp = CorporationOwnerFactory(user=self.manage_own_user)

        # Test Action
        response = self.client.delete(
            f"{self.api}/superuser/owners/corporation/{own_corp.eve_corporation.corporation_id}/"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_inspect_corporation_owner_should_return_404_for_unmanageable_owner(
        self,
    ):
        # Test Data
        self.client.force_login(self.manage_own_user)
        other_corp = CorporationOwnerFactory()

        # Test Action
        response = self.client.get(
            f"{self.api}/superuser/owners/corporation/{other_corp.eve_corporation.corporation_id}/inspect/"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_get_superuser_owners_should_include_alliances_and_unregistered_counts(
        self,
    ):
        # Test Data
        self.client.force_login(self.superuser)
        corp_owner = CorporationOwnerFactory()
        alliance = corp_owner.eve_corporation.alliance
        # Alliance without any corporation in audit
        other_alliance = EveAllianceInfoFactory()
        # Add an unregistered character to this corporation
        EveCharacterFactory(corporation=corp_owner.eve_corporation)
        # Add an unregistered corporation to this alliance
        EveCorporationInfoFactory(alliance=alliance)

        # Test Action
        response = self.client.get(f"{self.api}/superuser/owners/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        corp_entries = [
            item
            for item in data
            if item["owner_type"] == "corporation"
            and item["owner_id"] == corp_owner.eve_corporation.corporation_id
        ]
        self.assertEqual(len(corp_entries), 1)
        self.assertGreaterEqual(corp_entries[0]["unregistered_count"], 1)

        alliance_entries = [
            item
            for item in data
            if item["owner_type"] == "alliance"
            and item["owner_id"] == alliance.alliance_id
        ]
        self.assertEqual(len(alliance_entries), 1)
        self.assertEqual(alliance_entries[0]["status"], "ok")
        self.assertTrue(alliance_entries[0]["is_active"])
        self.assertGreaterEqual(alliance_entries[0]["unregistered_count"], 1)

        # Alliance without audit corporations must not be included
        other_alliance_entries = [
            item
            for item in data
            if item["owner_type"] == "alliance"
            and item["owner_id"] == other_alliance.alliance_id
        ]
        self.assertEqual(len(other_alliance_entries), 0)
