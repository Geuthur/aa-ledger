"""TestView class."""

from http import HTTPStatus

from django.test import RequestFactory, TestCase
from django.urls import reverse

from app_utils.testdata_factories import UserMainFactory
from app_utils.testing import (
    create_user_from_evecharacter,
)

from ledger.tests.testdata.generate_characteraudit import (
    create_user_from_evecharacter_with_access,
)
from ledger.tests.testdata.generate_corporationaudit import (
    add_corporationaudit_corporation_to_user,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse
from ledger.views.character import character_ledger
from ledger.views.corporation import corporation_ledger

CHARLEDGER_PATH = "ledger.views.character.character_ledger"


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

    def test_view_character_admin(self):
        """Test view character admin."""
        # given
        request = self.factory.get(reverse("ledger:character_admin"))
        request.user = self.user
        # when
        response = character_ledger.character_admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Ledger Character Overview")


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
            ],
        )

    def test_view_corporation_ledger(self):
        """Test view corporation ledger."""
        # given
        request = self.factory.get(
            reverse(
                "ledger:corporation_ledger",
                args=[self.character_ownership.character.character_id],
            )
        )
        request.user = self.user
        # when
        response = corporation_ledger.corporation_ledger(
            request, self.character_ownership.character.character_id
        )
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Corporation Ledger")

    def test_view_corporation_admin(self):
        """Test view corporation admin."""
        # given
        request = self.factory.get(reverse("ledger:corporation_admin"))
        request.user = self.user
        # when
        response = corporation_ledger.corporation_admin(request)
        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Ledger Corporation Overview")
