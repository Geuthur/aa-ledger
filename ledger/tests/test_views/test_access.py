"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Django
from django.urls import reverse

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import (
    add_new_permission_to_user,
    create_owner_from_user,
)
from ledger.views import index
from ledger.views.alliance import alliance_ledger
from ledger.views.character import character_ledger, planetary
from ledger.views.corporation import corporation_ledger

INDEX_PATH = "ledger.views.index"
CHARLEDGER_PATH = "ledger.views.character.character_ledger"
CORPLEDGER_PATH = "ledger.views.corporation.corporation_ledger"
ALLYLEDGER_PATH = "ledger.views.alliance.alliance_ledger"


@patch(INDEX_PATH + ".messages")
class TestViewIndexAccess(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_admin(self, mock_messages):
        """
        Test admin access.

        This test logs in a superuser and verifies that they can access the admin view.
        """
        # Test Data
        request = self.factory.get(reverse("ledger:admin"))
        request.user = self.superuser

        # Test Action
        response = index.admin(request)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Administration")

    def test_admin_no_access(self, mock_messages):
        """
        Test admin access.

        This test verifies that a user without admin access is redirected and an error message is shown.
        """
        # Test Data
        request = self.factory.get(reverse("ledger:admin"))
        request.user = self.user

        self._middleware_process_request(request)

        # Test Action
        response = index.admin(request)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(mock_messages.error.called)

    @patch(INDEX_PATH + ".clear_all_etags")
    def test_admin_clear_all_etags(self, mock_clear_etags, mock_messages):
        """
        Test clear all etags.

        This test posts to the admin view to trigger the clear etags action.
        """
        # Test Data
        request = self.factory.post(
            reverse("ledger:admin"), data={"run_clear_etag": True}
        )
        request.user = self.superuser
        self._middleware_process_request(request)

        # Test Action
        response = index.admin(request)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.info.assert_called_once_with(request, "Queued Clear All ETags")

    def test_force_refresh(self, mock_messages):
        """
        Test force refresh.

        This test posts to the admin view to trigger the force refresh action.
        """
        # Test Data
        request = self.factory.post(
            reverse("ledger:admin"), data={"force_refresh": True}
        )
        request.user = self.superuser
        self._middleware_process_request(request)

        # Test Action
        response = index.admin(request)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)

    @patch(INDEX_PATH + ".update_all_characters")
    def test_run_char_updates(self, mock_update_characters, mock_messages):
        """
        Test run char updates.

        This test posts to the admin view to trigger the run character updates action.
        """
        # Test Data
        request = self.factory.post(
            reverse("ledger:admin"), data={"run_char_updates": True}
        )
        request.user = self.superuser
        self._middleware_process_request(request)

        # Test Action
        response = index.admin(request)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.info.assert_called_once_with(
            request, "Queued Update All Characters"
        )

    @patch(INDEX_PATH + ".update_all_corporations")
    def test_run_corp_updates(self, mock_update_corporations, mock_messages):
        """
        Test Run corp updates.

        This test posts to the admin view to trigger the run corporation updates action.
        """
        # Test Data
        request = self.factory.post(
            reverse("ledger:admin"), data={"run_corp_updates": True}
        )
        request.user = self.superuser
        self._middleware_process_request(request)

        # Test Action
        response = index.admin(request)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.info.assert_called_once_with(
            request, "Queued Update All Corporations"
        )


class TestViewCharacterLedgerAccess(LedgerTestCase):
    """Test character ledger access."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = create_owner_from_user(
            user=cls.user,
            owner_type="character",
        )

    def test_view_character_ledger(self):
        """
        Test view character ledger.

        This test verifies that a user with permission can access their character ledger.
        """
        # Test Data
        request = self.factory.get(
            reverse(
                "ledger:character_ledger",
                kwargs={
                    "character_id": self.user_character.character.character_id,
                    "year": 2025,
                },
            )
        )
        request.user = self.user

        # Test Action
        response = character_ledger.character_ledger(
            request,
            character_id=self.user_character.character.character_id,
            year=2025,
        )
        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Character Ledger")

    @patch(CHARLEDGER_PATH + ".messages")
    def test_view_character_ledger_without_permission(self, mock_messages):
        """
        Test view character ledger without permission.

        This test verifies that a user without permission is shown an error message when accessing a character ledger.
        """
        # Test Action
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "ledger:character_ledger",
                kwargs={"character_id": 1003, "year": 2025},
            ),
            follow=True,
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Character Ledger")
        self.assertTrue(mock_messages.error.called)

    def test_view_character_overview(self):
        """
        Test view character overview.

        This test verifies that a user with permission can access the character overview.
        """
        # Test Data
        request = self.factory.get(reverse("ledger:character_overview"))
        request.user = self.user

        # Test Action
        response = character_ledger.character_overview(request)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Character Overview")

    def test_view_character_administration(self):
        """
        Test view character administration.

        This test verifies that a user with permission can access their character administration view.
        """
        # Test Data
        request = self.factory.get(
            reverse(
                "ledger:character_administration",
                kwargs={"character_id": self.user_character.character.character_id},
            )
        )
        request.user = self.user

        # Test Action
        response = character_ledger.character_administration(
            request, character_id=self.user_character.character.character_id
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Administration")

    def test_view_character_administration_withouth_character_id(self):
        """
        Test view character administration.

        This test verifies that a user with permission can access their character administration view without providing a character ID.
        """
        # Test Data
        request = self.factory.get(
            reverse(
                "ledger:character_administration",
                kwargs={"character_id": self.user_character.character.character_id},
            )
        )
        request.user = self.user

        # Test Action
        response = character_ledger.character_administration(request)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Administration")

    @patch(CHARLEDGER_PATH + ".messages")
    def test_view_character_administration_no_permission(self, mock_messages):
        """
        Test view character administration.

        This test verifies that a user without permission is redirected and shown an error message when accessing character administration.
        """
        # Test Data
        request = self.factory.get(
            reverse("ledger:character_administration", args=[1002])
        )
        request.user = self.user
        self._middleware_process_request(request)

        # Test Action
        response = character_ledger.character_administration(request, character_id=1002)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_once_with(request, "Permission Denied")


class TestViewCorporationLedgerAccess(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(
            user=cls.user,
            owner_type="corporation",
        )
        cls.user = add_new_permission_to_user(cls.user, "ledger.advanced_access")

    def test_view_corporation_ledger(self):
        """
        Test view corporation ledger.

        This test verifies that a user with permission can access their corporation ledger.
        """
        # Test Data
        request = self.factory.get(
            reverse(
                "ledger:corporation_ledger",
                kwargs={
                    "corporation_id": self.user_character.character.corporation_id,
                    "year": 2025,
                },
            )
        )
        request.user = self.user

        # Test Action
        response = corporation_ledger.corporation_ledger(
            request,
            corporation_id=self.user_character.character.corporation_id,
            year=2025,
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Corporation Ledger")

    @patch(CORPLEDGER_PATH + ".messages")
    def test_view_corporation_ledger_not_found(self, mock_messages):
        """
        Test view corporation ledger not found.

        This test verifies that a user is shown an info message when accessing a non-existent corporation ledger.
        """
        # Test Action
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "ledger:corporation_ledger",
                kwargs={"corporation_id": 9999, "year": 2025},
            ),
            follow=True,
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Corporation Ledger")
        self.assertTrue(mock_messages.info.called)

    @patch(CORPLEDGER_PATH + ".messages")
    def test_view_corporation_ledger_without_permission(self, mock_messages):
        """
        Test view corporation ledger without permission.

        This test verifies that a user without permission is shown an error message when accessing a corporation ledger.
        """
        # Test Data
        self.user2 = add_new_permission_to_user(self.user2, "ledger.advanced_access")
        # Test Action
        self.client.force_login(self.user2)
        response = self.client.get(
            reverse(
                "ledger:corporation_ledger",
                kwargs={"corporation_id": 2001, "year": 2025},
            ),
            follow=True,
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Corporation Ledger")
        self.assertTrue(mock_messages.error.called)

    def test_view_corporation_overview(self):
        """
        Test view corporation overview.

        This test verifies that a user with permission can access the corporation overview.
        """
        # Test Data
        request = self.factory.get(reverse("ledger:corporation_overview"))
        request.user = self.user

        # Test Action
        response = corporation_ledger.corporation_overview(request)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Corporation Overview")

    def test_view_corporation_administration(self):
        """
        Test view corporation administration.

        This test verifies that a user with permission can access their corporation administration view.
        """
        # Test Data
        request = self.factory.get(
            reverse(
                "ledger:corporation_administration",
                kwargs={"corporation_id": self.user_character.character.corporation_id},
            )
        )
        request.user = self.manage_own_user

        # Test Action
        response = corporation_ledger.corporation_administration(
            request, self.user_character.character.corporation_id
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Administration")

    @patch(CORPLEDGER_PATH + ".messages")
    def test_view_corporation_administration_no_permission(self, mock_messages):
        """
        Test view corporation administration.

        This test verifies that a user without permission is redirected and shown an error message when accessing corporation administration.
        """
        # Test Data
        create_owner_from_user(self.user2, owner_type="corporation")
        request = self.factory.get(
            reverse(
                "ledger:corporation_administration", kwargs={"corporation_id": 2002}
            )
        )
        request.user = self.manage_own_user
        self._middleware_process_request(request)

        # Test Action
        response = corporation_ledger.corporation_administration(
            request, corporation_id=2002
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_once_with(request, "Permission Denied")

    @patch(CORPLEDGER_PATH + ".messages")
    def test_view_corporation_administration_corporation_not_found(self, mock_messages):
        """
        Test view corporation administration.

        This test verifies that a user is redirected and shown an info message when accessing a non-existent corporation administration.
        """
        # Test Data
        request = self.factory.get(
            reverse(
                "ledger:corporation_administration", kwargs={"corporation_id": 6666}
            )
        )
        request.user = self.manage_own_user
        self._middleware_process_request(request)

        # Test Action
        response = corporation_ledger.corporation_administration(
            request, corporation_id=6666
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.info.assert_called_once_with(request, "Corporation not found")

    def test_view_corporation_data_exporter(self):
        """
        Test view corporation data exporter.

        This test verifies that a user with permission can access the corporation data exporter.
        """
        # Test Data
        request = self.factory.get(
            reverse("ledger:corporation_data_export", args=[2001])
        )
        request.user = self.superuser

        # Test Action
        response = corporation_ledger.corporation_data_export(request, 2001)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)

    @patch(CORPLEDGER_PATH + ".messages")
    def test_view_corporation_data_exporter_no_permission(self, mock_messages):
        """
        Test view corporation data exporter with no permission.

        This test verifies that a user without permission is shown an error message when accessing the corporation data exporter.
        """
        # Test Data
        request = self.factory.get(
            reverse("ledger:corporation_data_export", kwargs={"corporation_id": 2001})
        )
        request.user = self.user2
        self._middleware_process_request(request)

        # Test Action
        response = corporation_ledger.corporation_data_export(
            request, corporation_id=2001
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.error.assert_called_once_with(request, "Permission Denied")

    @patch(CORPLEDGER_PATH + ".messages")
    def test_view_corporation_data_exporter_not_found(self, mock_messages):
        """
        Test view corporation data exporter with not found corporation.

        This test verifies that a user is shown an info message when accessing a non-existent corporation data exporter.
        """
        # Test Data
        request = self.factory.get(
            reverse("ledger:corporation_data_export", args=[9999])
        )
        request.user = self.superuser
        self._middleware_process_request(request)

        # Test Action
        response = corporation_ledger.corporation_data_export(
            request, corporation_id=9999
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.info.assert_called_once_with(request, "Corporation not found")


class TestViewAllianceLedgerAccess(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = create_owner_from_user(user=cls.user, owner_type="corporation")
        cls.audit_admin = create_owner_from_user(
            user=cls.user2, owner_type="corporation"
        )
        cls.user = add_new_permission_to_user(cls.user, "ledger.advanced_access")
        cls.user2 = add_new_permission_to_user(cls.user2, "ledger.advanced_access")

    def test_view_alliance_ledger(self):
        """
        Test view alliance ledger.

        This test verifies that a user with permission can access their alliance ledger.
        """
        # Test Data
        request = self.factory.get(
            reverse(
                "ledger:alliance_ledger",
                kwargs={
                    "alliance_id": self.user_character.character.alliance_id,
                    "year": 2025,
                },
            )
        )
        request.user = self.user

        # Test Action
        response = alliance_ledger.alliance_ledger(
            request, alliance_id=self.user_character.character.alliance_id, year=2025
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Alliance Ledger")

    @patch(ALLYLEDGER_PATH + ".messages")
    def test_view_alliance_ledger_not_found(self, mock_messages):
        """
        Test view alliance ledger not found.

        This test verifies that a user is shown an info message when accessing a non-existent alliance ledger.
        """
        # Test Action
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "ledger:alliance_ledger", kwargs={"alliance_id": 9999, "year": 2025}
            ),
            follow=True,
        )

        # Expected Result: final page after redirect is OK and contains the overview
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Alliance Overview")
        self.assertTrue(mock_messages.info.called)

    @patch(ALLYLEDGER_PATH + ".messages")
    def test_view_alliance_ledger_without_permission(self, mock_messages):
        """
        Test view alliance ledger without permission.

        This test verifies that a user without permission is shown an error message when accessing an alliance ledger.
        """
        # Test Action
        self.client.force_login(self.user2)
        response = self.client.get(
            reverse(
                "ledger:alliance_ledger", kwargs={"alliance_id": 3001, "year": 2025}
            ),
            follow=True,
        )

        # Expected Result: final page after redirect is OK and shows overview, and an error message was created
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Alliance Overview")
        self.assertTrue(mock_messages.error.called)

    def test_view_alliance_overview(self):
        """
        Test view alliance overview.

        This test verifies that a user with permission can access the alliance overview.
        """
        # Test Data
        request = self.factory.get(reverse("ledger:alliance_overview"))
        request.user = self.user

        # Test Action
        response = alliance_ledger.alliance_overview(request)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Alliance Overview")

    def test_view_alliance_administration(self):
        """
        Test view alliance administration.

        This test verifies that a user with permission can access their alliance administration view.
        """
        # Test Data
        request = self.factory.get(
            reverse(
                "ledger:alliance_administration",
                kwargs={"alliance_id": self.user_character.character.alliance_id},
            )
        )
        request.user = self.manage_user

        # Test Action
        response = alliance_ledger.alliance_administration(
            request, alliance_id=self.user_character.character.alliance_id
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Administration")

    @patch(ALLYLEDGER_PATH + ".messages")
    def test_view_alliance_administration_no_permission(self, mock_messages):
        """
        Test view alliance administration without permission.

        This test verifies that a user without permission is redirected and shown an error message when accessing alliance administration.
        """
        # Test Data
        request = self.factory.get(
            reverse("ledger:alliance_administration", kwargs={"alliance_id": 3002})
        )
        request.user = self.manage_own_user
        self._middleware_process_request(request)

        # Test Action
        response = alliance_ledger.alliance_administration(request, alliance_id=3002)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_once_with(request, "Permission Denied")

    @patch(ALLYLEDGER_PATH + ".messages")
    def test_view_alliance_administration_alliance_not_found(self, mock_messages):
        """
        Test view alliance administration when the alliance is not found.

        This test verifies that a user is redirected and shown an info message when accessing a non-existent alliance administration.
        """
        # Test Data
        request = self.factory.get(
            reverse("ledger:alliance_administration", kwargs={"alliance_id": 6666})
        )
        request.user = self.manage_user
        self._middleware_process_request(request)

        # Test Action
        response = alliance_ledger.alliance_administration(request, alliance_id=6666)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.info.assert_called_once_with(request, "Alliance not found.")


class TestViewPlanetaryLedgerAccess(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = create_owner_from_user(
            user=cls.user,
        )
        cls.user = add_new_permission_to_user(cls.user, "ledger.advanced_access")

    def test_view_planetary_ledger_index(self):
        """Test view planetary ledger index."""
        # given
        request = self.factory.get(reverse("ledger:planetary_ledger_index"))
        request.user = self.user
        # when
        response = planetary.planetary_ledger_index(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_view_planetary_ledger(self):
        """Test view planetary ledger."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:planetary_ledger",
                args=[self.user_character.character.character_id],
            )
        )
        request.user = self.user
        # when
        response = planetary.planetary_ledger(
            request, self.user_character.character.character_id
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Planetary Details")

    def test_view_planetary_ledger_without_character_id(self):
        """Test view character ledger."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:planetary_ledger",
                args=[self.user_character.character.character_id],
            )
        )
        request.user = self.user
        # when
        response = planetary.planetary_ledger(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Planetary Details")

    def test_view_planetary_overview(self):
        """Test view planetary overview."""
        # given
        request = self.factory.get(reverse("ledger:planetary_overview"))
        request.user = self.user
        # when
        response = planetary.planetary_overview(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Planetary Overview")
