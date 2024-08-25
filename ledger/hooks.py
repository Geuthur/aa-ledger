""" AA Hooks"""

import logging

from ledger import app_settings
from ledger.errors import LedgerImportError


def get_extension_logger(name):
    """
    Takes the name of a plugin/extension and generates a child logger of the extensions logger
    to be used by the extension to log events to the extensions logger.

    The logging level is determined by the level defined for the parent logger.

    :param: name: the name of the extension doing the logging
    :return: an extensions child logger
    """

    logger_name = "ledger" if app_settings.LEDGER_LOGGER_USE else "extensions"

    if not isinstance(name, str):
        raise TypeError(
            f"get_extension_logger takes an argument of type string."
            f"Instead received argument of type {type(name).__name__}."
        )

    parent_logger = logging.getLogger(logger_name)

    logger = logging.getLogger(logger_name + "." + name)
    logger.name = name
    logger.level = parent_logger.level

    return logger


# pylint: disable=import-outside-toplevel
def get_corp_models_and_string():
    if app_settings.LEDGER_CORPSTATS_TWO:
        try:
            from corpstats.models import CorpMember

            return CorpMember
        except ImportError as exc:
            raise LedgerImportError("Corpstats is enabled but not installed") from exc

    from allianceauth.corputils.models import CorpMember

    return CorpMember


# pylint: disable=import-outside-toplevel, cyclic-import
def get_models_and_string():
    if app_settings.LEDGER_MEMBERAUDIT_USE:
        try:
            from memberaudit.models import (
                CharacterMiningLedgerEntry as CharacterMiningLedger,
            )
            from memberaudit.models import CharacterWalletJournalEntry

            return (
                CharacterMiningLedger,
                CharacterWalletJournalEntry,
            )
        except ImportError as exc:
            raise LedgerImportError("Memberaudit is enabled but not installed") from exc

    from ledger.models.characteraudit import (
        CharacterMiningLedger,
        CharacterWalletJournalEntry,
    )

    return (
        CharacterMiningLedger,
        CharacterWalletJournalEntry,
    )
