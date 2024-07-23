import sys
from unittest.mock import MagicMock, patch

from celery_once import AlreadyQueued
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
from app_utils.testing import add_character_to_user, create_user_from_evecharacter

from ledger.api.helpers import (
    _process_character,
    _process_missing_characters,
    get_alts_queryset,
    get_character,
    get_corp_models_and_string,
    get_main_and_alts_all,
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

        cls.user, cls.char_owner = create_user_from_evecharacter(
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
        cls.user5, _ = create_user_from_evecharacter(
            1005,
        )
        cls.corp = EveCorporationInfo.objects.get(corporation_id=2001)

    def test_get_main_and_alts_all_char_in_chars(self):
        # given
        mains = {}
        request = self.factory.get("/")
        request.user = self.user
        corp_stats = CorpStats.objects.create(
            token=Token.objects.get(user=self.user),
            corp=self.corp,
        )
        CorpMember.objects.create(
            character_id=1005, character_name="Gerthd", corpstats=corp_stats
        )
        chars = EveCharacter.objects.filter(
            corporation_id__in=[self.corp.corporation_id]
        )
        for char in chars:
            mains[char.character_id] = {"main": char, "alts": [char]}
        excepted_data = mains
        # when
        data, _ = get_main_and_alts_all([self.corp.corporation_id])
        # then
        self.assertEqual(data, excepted_data)

    @patch(MODULE_PATH + ".EveCharacter.objects.select_related")
    def test_get_main_and_alts_all_process_corpmember(self, mock_select_related):
        # given
        mock_char = MagicMock()
        mock_char.character_id = 1005
        mock_char.character_name = "Gerthd"
        mock_select_related.return_value.get.return_value = mock_char

        request = self.factory.get("/")
        request.user = self.user
        corp_stats = CorpStats.objects.create(
            token=Token.objects.get(user=self.user),
            corp=self.corp,
        )
        CorpMember.objects.create(
            character_id=9999, character_name="Test9999", corpstats=corp_stats
        )

        # when
        data, _ = get_main_and_alts_all([self.corp.corporation_id])
        # then
        mock_select_related.assert_called()
        self.assertIn("MagicMock", str(data.values()))

    @patch(MODULE_PATH + ".EveCharacter.objects.select_related")
    def test_get_main_and_alts_all_process_corpmember_object_does_not_exist(
        self, mock_select_related
    ):
        # Setup mock EveCharacter instance to simulate ObjectDoesNotExist
        mock_select_related.return_value.get.side_effect = ObjectDoesNotExist

        # Setup the rest of your test environment as before
        mains = {}
        request = self.factory.get("/")
        request.user = self.user
        corp_stats = CorpStats.objects.create(
            token=Token.objects.get(user=self.user),
            corp=self.corp,
        )
        CorpMember.objects.create(
            character_id=9999, character_name="Test9999", corpstats=corp_stats
        )
        chars = EveCharacter.objects.filter(
            corporation_id__in=[self.corp.corporation_id]
        )
        for char in chars:
            mains[char.character_id] = {"main": char, "alts": [char]}

        # when
        data, _ = get_main_and_alts_all([self.corp.corporation_id])

    def test_get_main_character(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        add_character_to_user(
            self.user, EveCharacter.objects.get(character_id=1004), is_main=False
        )
        data = get_character(request, 1004)
        character = EveCharacter.objects.get(character_id=1004)
        # then
        self.assertEqual(data, (True, character))

    def test_get_main_character_no_permission(self):
        # given
        request = self.factory.get("/")
        request.user = self.user3
        # when
        data = get_character(request, 1001)
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
        data = get_character(request, 1001)
        character = EveCharacter.objects.get(character_id=1001)
        # then
        self.assertEqual(data, (False, character))

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

    def test_process_character(self):
        # Create mock main character
        main_char = EveCharacter(character_id=1002, corporation_id=2002)

        # Mock char with a main character
        char = EveCharacter(character_id=1001, corporation_id=2001)
        char.character_ownership = self.char_owner
        char.character_ownership.user.profile.main_character = main_char

        # Test main not in characters
        characters = {}
        chars_list = set()
        corporations = {}
        missing_chars = set()

        _process_character(char, characters, chars_list, corporations, missing_chars)

        # Test main in characters
        characters = {1002: {"main": main_char, "alts": []}}
        chars_list = set()
        corporations = {}
        missing_chars = set()

        _process_character(char, characters, chars_list, corporations, missing_chars)

        # Test Corporation exist
        characters = {}
        chars_list = set()
        corporations = [2001]
        missing_chars = set()

        _process_character(char, characters, chars_list, corporations, missing_chars)

        # Test Corporation not exist
        char = EveCharacter(character_id=1001, corporation_id=2001)
        characters = {}
        chars_list = set()
        corporations = {}
        missing_chars = set()

        _process_character(char, characters, chars_list, corporations, missing_chars)

        # Test Attribute Error
        error = EveCorporationInfo.objects.get(corporation_id=2001)
        characters = {}
        chars_list = set()
        corporations = [2001]
        missing_chars = set()

        _process_character(error, characters, chars_list, corporations, missing_chars)

        # Test Missing character
        char = EveCharacter(character_id=9999, corporation_id=2001)
        characters = {}
        chars_list = set()
        corporations = []
        missing_chars = set()

        _process_character(char, characters, chars_list, corporations, missing_chars)


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


class TestApiHelperTask(TestCase):
    @patch(MODULE_PATH + ".create_missing_character.apply_async")
    def test_already_queued_exception(self, mock_apply_async):
        # Given
        missing_chars = {1001}

        # Configure the mock to raise AlreadyQueued on the second call
        mock_apply_async.side_effect = [None, AlreadyQueued(countdown=60)]

        # When: First call should pass without raising an exception
        _process_missing_characters(missing_chars)

        # Then: Second call should raise AlreadyQueued, which is caught and handled
        _process_missing_characters(missing_chars)

        # Assert apply_async was called twice
        self.assertEqual(mock_apply_async.call_count, 2)
