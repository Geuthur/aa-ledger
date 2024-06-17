from unittest.mock import MagicMock, patch

from django.core.exceptions import ObjectDoesNotExist
from django.test import RequestFactory, TestCase
from esi.models import Token

from allianceauth.corputils.models import CorpMember, CorpStats
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from app_utils.testing import (
    add_character_to_user,
    add_new_token,
    create_user_from_evecharacter,
)

from ledger.api.helpers import (
    get_alts_queryset,
    get_main_and_alts_all,
    get_main_character,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth

MODULE_PATH = "ledger.api.helpers"


class TestApiHelpers(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        cls.factory = RequestFactory()
        cls.user, _ = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
            ],
        )
        cls.user2, _ = create_user_from_evecharacter(
            1002,
            permissions=[
                "ledger.basic_access",
            ],
        )
        cls.user3, _ = create_user_from_evecharacter(
            1003,
        )
        cls.user4, _ = create_user_from_evecharacter(
            1004,
        )

    def test_get_main_and_alts_all_no_corp(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        char = EveCharacter.objects.get(character_id=1001)
        char2 = EveCharacter.objects.get(character_id=1004)
        self.user4.profile.main_character.delete()
        # when
        data = get_main_and_alts_all([2001], corp_members=False)
        # then
        self.assertEqual(
            data, {1001: {"main": char, "alts": []}, 1004: {"main": char2, "alts": []}}
        )

    def test_get_main_and_alts_all_with_and_char_not_in_chars(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        corp_stats = CorpStats.objects.create(
            token=Token.objects.get(user=self.user),
            corp=EveCorporationInfo.objects.get(corporation_id=2001),
        )
        CorpMember.objects.create(
            character_id=1005, character_name="Gerthd", corpstats=corp_stats
        )
        # when
        data = get_main_and_alts_all([2001], corp_members=True)
        # then
        char = EveCharacter.objects.get(character_id=1001)
        self.assertEqual(data, {1001: {"main": char, "alts": []}})

    def test_get_main_and_alts_all_with_and_char_in_chars(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        corp_stats = CorpStats.objects.create(
            token=Token.objects.get(user=self.user),
            corp=EveCorporationInfo.objects.get(corporation_id=2001),
        )
        CorpMember.objects.create(
            character_id=1005, character_name="Gerthd", corpstats=corp_stats
        )
        self.user5, _ = create_user_from_evecharacter(
            1005,
        )
        # when
        data = get_main_and_alts_all([2001], corp_members=True)
        # then
        char = EveCharacter.objects.get(character_id=1001)
        self.assertEqual(data, {1001: {"main": char, "alts": []}})

    def test_get_main_character(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        add_character_to_user(
            self.user, EveCharacter.objects.get(character_id=1004), is_main=False
        )
        data = get_main_character(request, 1004)
        character = EveCharacter.objects.get(character_id=1001)
        # then
        self.assertEqual(data, (True, character))

    def test_get_main_character_no_permission(self):
        # given
        request = self.factory.get("/")
        request.user = self.user3
        # when
        data = get_main_character(request, 1001)
        character = EveCharacter.objects.get(character_id=1001)
        # then
        self.assertEqual(data, (False, character))

    @patch(MODULE_PATH + ".models.CharacterAudit.objects.visible_eve_characters")
    def test_main_char_not_in_account_chars(self, mock_visible):
        # given
        request = self.factory.get("/")
        mock_visible.return_value = []
        request.user = self.user
        # when
        data = get_main_character(request, 1001)
        character = EveCharacter.objects.get(character_id=1001)
        # then
        self.assertEqual(data, (True, character))

    def test_get_alts_queryset(self):
        # given
        main_char = EveCharacter.objects.get(character_id=1001)
        # when
        data = get_alts_queryset(main_char)
        # then
        self.assertEqual(data.count(), 1)

    def test_get_alts_queryset_no_linked_characters(self):
        # given
        main_char = MagicMock()
        main_char.character_ownership.user.character_ownerships.all.return_value.values_list.side_effect = (
            ObjectDoesNotExist
        )
        main_char.pk = 90
        # when
        data = get_alts_queryset(main_char)
        # then
        self.assertEqual(data.count(), 1)
