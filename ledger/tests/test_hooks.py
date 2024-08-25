import sys
from unittest.mock import patch

from django.test import TestCase

from ledger.errors import LedgerImportError
from ledger.hooks import (
    get_corp_models_and_string,
    get_extension_logger,
    get_models_and_string,
)

MODULE_PATH = "ledger.hooks"


class TestTemplateTags(TestCase):
    def test_logger_fail(self):
        with self.assertRaises(TypeError):
            get_extension_logger(1234)


class TestApiHelperCorpStatsImport(TestCase):
    def setUp(self):
        self.original_sys_modules = sys.modules.copy()

    def tearDown(self):
        sys.modules = self.original_sys_modules

    @patch(MODULE_PATH + ".app_settings.LEDGER_CORPSTATS_TWO", True)
    @patch(MODULE_PATH + ".app_settings.LEDGER_MEMBERAUDIT_USE", True)
    def test_packages_are_not_installed(self):
        with patch.dict(
            sys.modules,
            {k: None for k in list(sys.modules) if k.startswith("corpstats")},
        ):
            with self.assertRaises(LedgerImportError):
                _ = get_corp_models_and_string()

        with patch.dict(
            sys.modules,
            {k: None for k in list(sys.modules) if k.startswith("memberaudit")},
        ):
            with self.assertRaises(LedgerImportError):
                CharacterMiningLedger, CharacterWalletJournalEntry = (
                    get_models_and_string()
                )
