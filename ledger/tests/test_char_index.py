from unittest.mock import Mock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse

from allianceauth.eveonline.models import EveCharacter
from allianceauth.tests.auth_utils import AuthUtils
from app_utils.testdata_factories import UserMainFactory

from ledger.models.characteraudit import CharacterAudit
from ledger.tasks import update_character


class AddCharTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = AuthUtils.create_user("User1")

        char1 = EveCharacter.object.create(
            character_id=1,
            character_name="character.name1",
            corporation_id=1337,
            corporation_name="corporation.name1",
            corporation_ticker="ABC",
        )

        CharacterAudit.objects.update_or_create(
            character=EveCharacter.objects.get_character_by_id(char1.character_id)
        )

        update_character.apply_async(
            args=[char1.character_id], kwargs={"force_refresh": True}, priority=6
        )


class FetchMemberAuditTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(
            permissions=[
                "ledger.basic_access",
            ]
        )

    def test_fetch_memberaudit(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("ledger:ledger_fetch_memberaudit"))

        self.assertEqual(response.status_code, 302)
