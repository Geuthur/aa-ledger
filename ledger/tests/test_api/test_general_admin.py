# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Django
from django.urls import reverse

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import CharacterOwnerFactory, CorporationOwnerFactory

TASKS_PATH = "ledger.api.general.tasks"


class TestGeneralApi(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = f"{reverse('ledger:index')}api"

    def test_get_menu_should_hide_advanced_links_without_permission(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.api}/menu/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        links = [link["link"] for link in response.json()["left_links"]]
        self.assertEqual(links, ["/", "/planetary/"])
        right_links = [link["link"] for link in response.json()["right_links"]]
        self.assertEqual(right_links, [reverse("ledger:add_char"), "/settings/"])

    def test_get_menu_should_show_advanced_and_admin_links(self):
        # Test Data
        self.client.force_login(self.manage_user)
        self.manage_user.is_superuser = True
        self.manage_user.save()

        # Test Action
        response = self.client.get(f"{self.api}/menu/")

        # Expected Result
        data = response.json()
        links = [link["link"] for link in data["left_links"]]
        self.assertIn("/corporation/", links)
        self.assertIn("/alliance/", links)
        right_links = [link["link"] for link in data["right_links"]]
        self.assertIn(reverse("ledger:add_corp"), right_links)
        self.assertIn(reverse("ledger:add_ally"), right_links)
        self.assertEqual(data["right_links"][-1]["link"], "/admin/")

    def test_get_menu_should_return_403_without_basic_access(self):
        # Test Data
        user = self.user
        user.user_permissions.clear()
        self.client.force_login(user)

        # Test Action
        with patch.object(type(user), "has_perm", return_value=False):
            response = self.client.get(f"{self.api}/menu/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_user_should_return_main_character_and_permissions(self):
        # Test Data
        self.client.force_login(self.manage_user)

        # Test Action
        response = self.client.get(f"{self.api}/user/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(data["character_id"], self.manage_character.character_id)
        self.assertTrue(data["can_manage"])
        self.assertTrue(data["has_advanced_access"])
        self.assertFalse(data["is_admin"])

    @patch(TASKS_PATH)
    def test_queue_update_should_queue_all_characters(self, mock_tasks):
        # Test Data
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(
            f"{self.api}/admin/update/",
            data={"target": "characters", "force_refresh": True},
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_tasks.update_all_characters.apply_async.assert_called_once_with(
            kwargs={"force_refresh": True}, priority=7
        )

    @patch(TASKS_PATH)
    def test_queue_update_should_queue_single_corporation(self, mock_tasks):
        # Test Data
        audit = CorporationOwnerFactory(user=self.manage_user)
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(
            f"{self.api}/admin/update/",
            data={"target": "corporations", "eve_id": audit.eve_id},
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_tasks.update_corporation.apply_async.assert_called_once_with(
            kwargs={"eve_id": audit.eve_id, "force_refresh": False}, priority=7
        )

    @patch(TASKS_PATH)
    def test_queue_update_should_return_404_for_unknown_character(self, mock_tasks):
        # Test Data
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(
            f"{self.api}/admin/update/",
            data={"target": "characters", "eve_id": 1},
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        mock_tasks.update_character.apply_async.assert_not_called()

    @patch(TASKS_PATH)
    def test_queue_update_should_return_403_for_non_superuser(self, mock_tasks):
        # Test Data
        self.client.force_login(self.manage_user)

        # Test Action
        response = self.client.post(
            f"{self.api}/admin/update/",
            data={"target": "characters"},
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        mock_tasks.update_all_characters.apply_async.assert_not_called()

    def test_get_settings_should_create_defaults(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.api}/settings/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(response.json()["disable_notifications"])

    def test_update_settings_should_persist_notification_flag(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.put(
            f"{self.api}/settings/",
            data={"disable_notifications": True},
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.json()["disable_notifications"])
        self.assertTrue(self.user.ledger_settings.disable_notifications)


class TestAdminApi(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = f"{reverse('ledger:index')}api"
        cls.character_owner = CharacterOwnerFactory(user=cls.user)
        cls.corporation_owner = CorporationOwnerFactory(user=cls.manage_user)

    def test_character_overview_should_list_visible_main_characters(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{self.api}/character/overview/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        ids = [row["character_id"] for row in response.json()]
        self.assertEqual(ids, [self.user_character.character_id])

    def test_corporation_overview_should_list_visible_corporations(self):
        # Test Data
        self.client.force_login(self.manage_user)

        # Test Action
        response = self.client.get(f"{self.api}/corporation/overview/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        ids = [row["corporation_id"] for row in response.json()]
        self.assertIn(self.corporation_owner.eve_id, ids)

    def test_alliance_overview_should_list_visible_alliances(self):
        # Test Data
        self.client.force_login(self.manage_user)

        # Test Action
        response = self.client.get(f"{self.api}/alliance/overview/")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.json()), 1)
