import sys
from unittest.mock import MagicMock, patch

from corpstats.models import CorpMember as ExpectedCorpMember
from memberaudit.models import (
    CharacterMiningLedgerEntry as ExceptedCharacterMiningLedger,
)
from memberaudit.models import (
    CharacterWalletJournalEntry as ExceptedCharacterWalletJournalEntry,
)

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
    get_corp_models_and_string,
    get_main_and_alts_all,
    get_main_character,
    get_models_and_string,
)
from ledger.errors import LedgerImportError
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
        self.user4.profile.main_character.delete()
        # when
        data = get_main_and_alts_all([2001], corp_members=False)
        # then
        self.assertEqual(data, {1001: {"main": char, "alts": []}})

    def test_get_main_and_alts_all_not_in_chars(self):
        # given
        mains = {}
        request = self.factory.get("/")
        request.user = self.user
        corp_stats = CorpStats.objects.create(
            token=Token.objects.get(user=self.user),
            corp=EveCorporationInfo.objects.get(corporation_id=2001),
        )
        CorpMember.objects.create(
            character_id=1005, character_name="Gerthd", corpstats=corp_stats
        )
        chars = EveCharacter.objects.filter(character_id__in=[1001, 1004, 1005])
        for char in chars:
            mains[char.character_id] = {"main": char, "alts": []}
        excepted_data = mains
        # when
        data = get_main_and_alts_all([2001], corp_members=True)
        # then
        self.assertEqual(data, excepted_data)

    def test_get_main_and_alts_all_char_in_chars(self):
        # given
        mains = {}
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
        chars = EveCharacter.objects.filter(character_id__in=[1001, 1004, 1005])
        for char in chars:
            mains[char.character_id] = {"main": char, "alts": []}
        excepted_data = mains
        # when
        data = get_main_and_alts_all([2001], corp_members=True)
        # then
        self.assertEqual(data, excepted_data)

    def test_get_main_and_alts_all_char_does_not_exist(self):
        # given
        mains = {}
        request = self.factory.get("/")
        request.user = self.user
        corp_stats = CorpStats.objects.create(
            token=Token.objects.get(user=self.user),
            corp=EveCorporationInfo.objects.get(corporation_id=2001),
        )
        corp_member = CorpMember.objects.create(
            character_id=1005, character_name="Gerthd", corpstats=corp_stats
        )
        EveCharacter.objects.get(character_id=1005).delete()

        chars = EveCharacter.objects.filter(character_id__in=[1001, 1004])
        for char in chars:
            mains[char.character_id] = {"main": char, "alts": []}
        mains[1005] = {"main": corp_member, "alts": []}

        excepted_data = mains
        # when
        data = get_main_and_alts_all([2001], corp_members=True)
        # then
        self.assertEqual(data, excepted_data)

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

        existing_char = EveCharacter.objects.all().first()
        main_char.pk = existing_char.pk

        # when
        data = get_alts_queryset(main_char)
        # then
        self.assertEqual(data.count(), 1)

    @patch(MODULE_PATH + ".app_settings.LEDGER_MEMBERAUDIT_USE", True)
    def test_get_models_and_string_memberaudit(self):
        CharacterMiningLedger, CharacterWalletJournalEntry = get_models_and_string()

        self.assertIs(CharacterMiningLedger, ExceptedCharacterMiningLedger)
        self.assertIs(CharacterWalletJournalEntry, ExceptedCharacterWalletJournalEntry)

    @patch(MODULE_PATH + ".app_settings.LEDGER_CORPSTATS_TWO", True)
    def test_get_corp_models_and_string(self):
        CorpMember = get_corp_models_and_string()
        self.assertIs(CorpMember, ExpectedCorpMember)


class TestApiHelperCorpStatsImport(TestCase):
    def setUp(self):
        self.original_sys_modules = sys.modules.copy()

    def tearDown(self):
        sys.modules = self.original_sys_modules

    @patch(MODULE_PATH + ".app_settings.LEDGER_CORPSTATS_TWO", True)
    @patch(MODULE_PATH + ".app_settings.LEDGER_MEMBERAUDIT_USE", True)
    @patch(MODULE_PATH + ".logger")
    def test_packages_are_not_installed(self, mock_logger):
        with patch.dict(
            sys.modules,
            {k: None for k in list(sys.modules) if k.startswith("corpstats")},
        ):
            with self.assertRaises(LedgerImportError):
                _ = get_corp_models_and_string()
            mock_logger.error.assert_called()

        with patch.dict(
            sys.modules,
            {k: None for k in list(sys.modules) if k.startswith("memberaudit")},
        ):
            with self.assertRaises(LedgerImportError):
                CharacterMiningLedger, CharacterWalletJournalEntry = (
                    get_models_and_string()
                )
            mock_logger.error.assert_called()
