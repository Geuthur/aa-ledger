"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Alliance Auth (External Libs)
from app_utils.testing import (
    create_user_from_evecharacter,
)

# AA Ledger
from ledger.tests.testdata.generate_characteraudit import (
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

    def test_view_character_ledger_index(self):
        """Test view character ledger index."""
        # given
        request = self.factory.get(reverse("ledger:character_ledger_index"))
        request.user = self.user
        # when
        response = character_ledger.character_ledger_index(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

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

    def test_view_character_ledger_without_character_id(self):
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
        response = character_ledger.character_ledger(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Character Ledger")

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

    def test_view_corporation_ledger_without_corporation_id(self):
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
        response = corporation_ledger.corporation_ledger(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Corporation Ledger")

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

    @patch(ALLYLEDGER_PATH + ".messages")
    def test_view_alliance_ledger_index_exception(self, mock_messages):
        """Test view alliance ledger."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:alliance_ledger_index",
            )
        )
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        request.user = self.user_has_no_alliance
        # when
        response = alliance_ledger.alliance_ledger_index(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_once_with(
            request, "You do not have an alliance."
        )

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
        mock_messages.info.assert_called_once_with(request, "Alliance not Found")


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
