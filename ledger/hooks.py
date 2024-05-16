""" AA Hooks"""

import logging

from ledger.app_settings import LEDGER_LOGGER_USE


def get_extension_logger(name):
    """
    Takes the name of a plugin/extension and generates a child logger of the extensions logger
    to be used by the extension to log events to the extensions logger.

    The logging level is determined by the level defined for the parent logger.

    :param: name: the name of the extension doing the logging
    :return: an extensions child logger
    """

    logger_name = "ledger" if LEDGER_LOGGER_USE else "extensions"

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
