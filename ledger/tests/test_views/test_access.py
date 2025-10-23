"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Alliance Auth (External Libs)
from app_utils.testing import (
    create_user_from_evecharacter,
)

# AA Ledger
from ledger.tests.testdata.generate_characteraudit import (
    add_characteraudit_character_to_user,
    create_user_from_evecharacter_with_access,
)
from ledger.tests.testdata.generate_corporationaudit import (
    add_corporationaudit_corporation_to_user,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse
from ledger.views import index
from ledger.views.alliance import alliance_ledger
from ledger.views.character import character_ledger, planetary
from ledger.views.corporation import corporation_ledger

INDEX_PATH = "ledger.views.index"
CHARLEDGER_PATH = "ledger.views.character.character_ledger"
CORPLEDGER_PATH = "ledger.views.corporation.corporation_ledger"
ALLYLEDGER_PATH = "ledger.views.alliance.alliance_ledger"


@patch(INDEX_PATH + ".messages")
class TestViewIndexAccess(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1002
        )
        cls.superuser, cls.character_ownership = (
            create_user_from_evecharacter_with_access(1001)
        )

    def test_admin(self, mock_messages):
        """Test admin access."""
        # given
        self.superuser.is_superuser = True
        self.superuser.save()

        request = self.factory.get(reverse("ledger:admin"))
        request.user = self.superuser
        # when
        response = index.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Administration")

    def test_admin_no_access(self, mock_messages):
        """Test admin access."""
        # given
        request = self.factory.get(reverse("ledger:admin"))
        request.user = self.user

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = index.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(mock_messages.error.called)

    def test_admin_clear_all_etags(self, mock_messages):
        """Test clear all etags."""
        # given
        self.superuser.is_superuser = True
        self.superuser.save()
        request = self.factory.post(
            reverse("ledger:admin"), data={"run_clear_etag": True}
        )
        request.user = self.superuser

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = index.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.info.assert_called_once_with(request, "Queued Clear All ETags")

    def test_force_refresh(self, mock_messages):
        """Test force refresh."""
        # given
        self.superuser.is_superuser = True
        self.superuser.save()
        request = self.factory.post(
            reverse("ledger:admin"), data={"force_refresh": True}
        )
        request.user = self.superuser

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = index.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_run_char_updates(self, mock_messages):
        """Test run char updates."""
        # given
        self.superuser.is_superuser = True
        self.superuser.save()
        request = self.factory.post(
            reverse("ledger:admin"), data={"run_char_updates": True}
        )
        request.user = self.superuser

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = index.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.info.assert_called_once_with(
            request, "Queued Update All Characters"
        )

    def test_run_corp_updates(self, mock_messages):
        """Test Run corp updates."""
        # given
        self.superuser.is_superuser = True
        self.superuser.save()
        request = self.factory.post(
            reverse("ledger:admin"), data={"run_corp_updates": True}
        )
        request.user = self.superuser

        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = index.admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.info.assert_called_once_with(
            request, "Queued Update All Corporations"
        )


class TestViewCharacterLedgerAccess(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )
        cls.user2, cls.character_ownership2 = create_user_from_evecharacter_with_access(
            1002
        )
        cls.audit = add_characteraudit_character_to_user(
            cls.user, cls.character_ownership.character.character_id
        )

    def test_view_character_ledger(self):
        """Test view character ledger."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:character_ledger",
                args=[self.character_ownership.character.character_id],
            )
        )
        request.user = self.user
        # when
        response = character_ledger.character_ledger(
            request, self.character_ownership.character.character_id
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Character Ledger")

    @patch(CHARLEDGER_PATH + ".messages")
    def test_view_character_ledger_without_permission(self, mock_messages):
        """Test view character ledger without permission."""
        # given
        request = self.factory.get(reverse("ledger:character_ledger", args=[1003]))
        request.user = self.user

        # Add session middleware to process the request
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        message_middleware = MessageMiddleware(Mock())
        message_middleware.process_request(request)
        # when
        response = character_ledger.character_ledger(request, 1003)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Character Ledger")
        self.assertTrue(mock_messages.error.called)

    def test_view_character_details(self):
        """Test view character details."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:character_details",
                args=[self.character_ownership.character.character_id, 2025],
            )
        )
        request.user = self.user
        # when
        response = character_ledger.character_details(
            request, self.character_ownership.character.character_id, year=2025
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response,
            "No ratting data found...",
        )

    def test_view_character_details_no_permission(self):
        """Test view character details."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:character_details",
                args=[self.character_ownership.character.character_id, 2025],
            )
        )
        request.user = self.user2

        # when
        response = character_ledger.character_details(
            request, self.character_ownership.character.character_id, year=2025
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Permission Denied")

    def test_view_character_overview(self):
        """Test view character overview."""
        # given
        request = self.factory.get(reverse("ledger:character_overview"))
        request.user = self.user
        # when
        response = character_ledger.character_overview(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Character Overview")

    def test_view_character_administration(self):
        """Test view character administration."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:character_administration",
                args=[self.character_ownership.character.character_id],
            )
        )
        request.user = self.user
        # when
        response = character_ledger.character_administration(
            request, self.character_ownership.character.character_id
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Administration")

    def test_view_character_administration_withouth_character_id(self):
        """Test view character administration."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:character_administration",
                args=[self.character_ownership.character.character_id],
            )
        )
        request.user = self.user
        # when
        response = character_ledger.character_administration(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Administration")

    @patch(CHARLEDGER_PATH + ".messages")
    def test_view_character_administration_no_permission(self, mock_messages):
        """Test view character administration."""
        # given
        request = self.factory.get(
            reverse("ledger:character_administration", args=[1002])
        )
        request.user = self.user
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = character_ledger.character_administration(request, 1002)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_once_with(request, "Permission Denied")


class TestViewCorporationLedgerAccess(TestCase):
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
                "ledger.manage_access",
                "ledger.corp_audit_manager",
            ],
        )
        cls.user_no_perm, cls.character_ownership_no_perm = (
            create_user_from_evecharacter(
                1002,
                permissions=[
                    "ledger.basic_access",
                    "ledger.advanced_access",
                    "ledger.manage_access",
                ],
            )
        )
        cls.audit = add_corporationaudit_corporation_to_user(cls.user, 1001)

    def test_view_corporation_ledger_index(self):
        """Test view corporation ledger index."""
        # given
        request = self.factory.get(reverse("ledger:corporation_ledger_index"))
        request.user = self.user
        # when
        response = corporation_ledger.corporation_ledger_index(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_view_corporation_ledger(self):
        """Test view corporation ledger."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:corporation_ledger",
                args=[self.character_ownership.character.corporation_id],
            )
        )
        request.user = self.user
        # when
        response = corporation_ledger.corporation_ledger(
            request, self.character_ownership.character.corporation_id
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Corporation Ledger")

    @patch(CORPLEDGER_PATH + ".messages")
    def test_view_corporation_ledger_not_found(self, mock_messages):
        """Test view corporation ledger not found."""
        # given
        request = self.factory.get(reverse("ledger:corporation_ledger", args=[9999]))
        request.user = self.user

        # Add session middleware to process the request
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        message_middleware = MessageMiddleware(Mock())
        message_middleware.process_request(request)
        # when
        response = corporation_ledger.corporation_ledger(request, 9999)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Corporation Ledger")
        self.assertTrue(mock_messages.info.called)

    @patch(CORPLEDGER_PATH + ".messages")
    def test_view_corporation_ledger_without_permission(self, mock_messages):
        """Test view corporation ledger without permission."""
        # given
        request = self.factory.get(reverse("ledger:corporation_ledger", args=[2001]))
        request.user = self.user_no_perm

        # Add session middleware to process the request
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        message_middleware = MessageMiddleware(Mock())
        message_middleware.process_request(request)
        # when
        response = corporation_ledger.corporation_ledger(request, 2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Corporation Ledger")
        self.assertTrue(mock_messages.error.called)

    def test_view_corporation_details(self):
        """Test view corporation details."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:corporation_details",
                args=[self.character_ownership.character.corporation_id, 2025, 1001],
            )
        )
        request.user = self.user
        # when
        response = corporation_ledger.corporation_details(
            request,
            self.character_ownership.character.corporation_id,
            entity_id=1001,
            year=2025,
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "No ratting data found...")

    def test_view_corporation_details_no_permission(self):
        """Test view corporation details."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:corporation_details",
                args=[2001, 2025, 1001],
            )
        )
        request.user = self.user_no_perm

        # when
        response = corporation_ledger.corporation_details(
            request, 2001, entity_id=1001, year=2025
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Permission Denied")

    def test_view_corporation_details_not_found(self):
        """Test view corporation details."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:corporation_details",
                args=[9999, 2025, 9999],
            )
        )
        request.user = self.user_no_perm

        # when
        response = corporation_ledger.corporation_details(
            request, 9999, entity_id=9999, year=2025
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Corporation not found")

    def test_view_corporation_overview(self):
        """Test view corporation overview."""
        # given
        request = self.factory.get(reverse("ledger:corporation_overview"))
        request.user = self.user
        # when
        response = corporation_ledger.corporation_overview(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Corporation Overview")

    def test_view_corporation_administration(self):
        """Test view corporation administration."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:corporation_administration",
                args=[self.character_ownership.character.corporation_id],
            )
        )
        request.user = self.user
        # when
        response = corporation_ledger.corporation_administration(
            request, self.character_ownership.character.corporation_id
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Administration")

    @patch(CORPLEDGER_PATH + ".messages")
    def test_view_corporation_administration_no_permission(self, mock_messages):
        """Test view corporation administration."""
        # given
        request = self.factory.get(
            reverse("ledger:corporation_administration", args=[2001])
        )
        request.user = self.user_no_perm
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = corporation_ledger.corporation_administration(request, 2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_once_with(request, "Permission Denied")

    @patch(CORPLEDGER_PATH + ".messages")
    def test_view_corporation_administration_corporation_not_found(self, mock_messages):
        """Test view corporation administration."""
        # given
        request = self.factory.get(
            reverse("ledger:corporation_administration", args=[6666])
        )
        request.user = self.user
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = corporation_ledger.corporation_administration(request, 6666)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.info.assert_called_once_with(request, "Corporation not found")

    def test_view_corporation_data_exporter(self):
        """Test view corporation data exporter."""
        # given
        request = self.factory.get(
            reverse("ledger:corporation_data_export", args=[2001])
        )
        request.user = self.user
        # when
        response = corporation_ledger.corporation_data_export(request, 2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)

    @patch(CORPLEDGER_PATH + ".messages")
    def test_view_corporation_data_exporter_no_permission(self, mock_messages):
        """Test view corporation data exporter with no permission."""
        # given
        request = self.factory.get(
            reverse("ledger:corporation_data_export", args=[2001])
        )
        request.user = self.user_no_perm
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = corporation_ledger.corporation_data_export(request, 2001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.error.assert_called_once_with(request, "Permission Denied")

    @patch(CORPLEDGER_PATH + ".messages")
    def test_view_corporation_data_exporter_not_found(self, mock_messages):
        """Test view corporation data exporter with not found corporation."""
        # given
        request = self.factory.get(
            reverse("ledger:corporation_data_export", args=[9999])
        )
        request.user = self.user
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = corporation_ledger.corporation_data_export(request, 9999)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_messages.info.assert_called_once_with(request, "Corporation not found")


class TestViewAllianceLedgerAccess(TestCase):
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
            ],
        )
        cls.user_no_perm, cls.character_ownership_no_perm = (
            create_user_from_evecharacter(
                1003,
                permissions=[
                    "ledger.basic_access",
                    "ledger.advanced_access",
                ],
            )
        )
        cls.user_admin, cls.character_ownership_admin = create_user_from_evecharacter(
            1002,
            permissions=[
                "ledger.basic_access",
                "ledger.advanced_access",
                "ledger.manage_access",
            ],
        )
        cls.audit = add_corporationaudit_corporation_to_user(cls.user, 1001)
        cls.audit_admin = add_corporationaudit_corporation_to_user(cls.user_admin, 1002)
        cls.user_has_no_alliance, cls.character_ownership_no_alliance = (
            create_user_from_evecharacter(
                1000,
                permissions=[
                    "ledger.basic_access",
                    "ledger.advanced_access",
                ],
            )
        )

    def test_view_alliance_ledger_index(self):
        """Test view alliance ledger index."""
        # given
        request = self.factory.get(reverse("ledger:alliance_ledger_index"))
        request.user = self.user
        # when
        response = alliance_ledger.alliance_ledger_index(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_view_alliance_ledger(self):
        """Test view alliance ledger."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:alliance_ledger",
                args=[self.character_ownership.character.alliance_id],
            )
        )
        request.user = self.user
        # when
        response = alliance_ledger.alliance_ledger(
            request, self.character_ownership.character.alliance_id
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Alliance Ledger")

    @patch(ALLYLEDGER_PATH + ".messages")
    def test_view_alliance_ledger_not_found(self, mock_messages):
        """Test view alliance ledger not found."""
        # given
        request = self.factory.get(reverse("ledger:alliance_ledger", args=[9999]))
        request.user = self.user

        # Add session middleware to process the request
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        message_middleware = MessageMiddleware(Mock())
        message_middleware.process_request(request)
        # when
        response = alliance_ledger.alliance_ledger(request, 9999)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Alliance Ledger")
        self.assertTrue(mock_messages.info.called)

    @patch(ALLYLEDGER_PATH + ".messages")
    def test_view_alliance_ledger_without_permission(self, mock_messages):
        """Test view alliance ledger without permission."""
        # given
        request = self.factory.get(reverse("ledger:alliance_ledger", args=[3001]))
        request.user = self.user_no_perm

        # Add session middleware to process the request
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        message_middleware = MessageMiddleware(Mock())
        message_middleware.process_request(request)
        # when
        response = alliance_ledger.alliance_ledger(request, 3001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Alliance Ledger")
        self.assertTrue(mock_messages.error.called)

    def test_view_alliance_details(self):
        """Test view alliance details."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:alliance_details",
                args=[self.character_ownership.character.alliance_id, 2025, 1001],
            )
        )
        request.user = self.user
        # when
        response = alliance_ledger.alliance_details(
            request,
            self.character_ownership.character.alliance_id,
            entity_id=1001,
            year=2025,
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "No ratting data found...")

    def test_view_alliance_details_no_permission(self):
        """Test view alliance details without permission."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:alliance_details",
                args=[3001, 2025, 2001],
            )
        )
        request.user = self.user_no_perm

        # when
        response = alliance_ledger.alliance_details(
            request, 3001, entity_id=2001, year=2025
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Permission Denied")

    def test_view_alliance_details_not_found(self):
        """Test view alliance details not found."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:alliance_details",
                args=[9999, 2025, 9999],
            )
        )
        request.user = self.user_no_perm

        # when
        response = alliance_ledger.alliance_details(
            request, 9999, entity_id=9999, year=2025
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Alliance not found.")

    def test_view_alliance_overview(self):
        """Test view alliance overview."""
        # given
        request = self.factory.get(reverse("ledger:alliance_overview"))
        request.user = self.user
        # when
        response = alliance_ledger.alliance_overview(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Alliance Overview")

    def test_view_alliance_administration(self):
        """Test view alliance administration."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:alliance_administration",
                args=[self.character_ownership_admin.character.alliance_id],
            )
        )
        request.user = self.user_admin
        # when
        response = alliance_ledger.alliance_administration(
            request, self.character_ownership_admin.character.alliance_id
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Administration")

    @patch(ALLYLEDGER_PATH + ".messages")
    def test_view_alliance_administration_no_permission(self, mock_messages):
        """Test view alliance administration."""
        # given
        request = self.factory.get(
            reverse("ledger:alliance_administration", args=[3001])
        )
        request.user = self.user_admin
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = alliance_ledger.alliance_administration(request, 3001)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_once_with(request, "Permission Denied")

    @patch(ALLYLEDGER_PATH + ".messages")
    def test_view_alliance_administration_alliance_not_found(self, mock_messages):
        """Test view alliance administration."""
        # given
        request = self.factory.get(
            reverse("ledger:alliance_administration", args=[6666])
        )
        request.user = self.user_admin
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        # when
        response = alliance_ledger.alliance_administration(request, 6666)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.info.assert_called_once_with(request, "Alliance not found.")


class TestViewPlanetaryLedgerAccess(TestCase):
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
            ],
        )

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
                args=[self.character_ownership.character.character_id],
            )
        )
        request.user = self.user
        # when
        response = planetary.planetary_ledger(
            request, self.character_ownership.character.character_id
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
                args=[self.character_ownership.character.character_id],
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
