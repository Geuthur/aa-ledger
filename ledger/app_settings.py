"""
App Settings
"""

import sys

# Django
from app_utils.app_settings import clean_setting

IS_TESTING = sys.argv[1:2] == ["test"]

# Set Test Mode True or False

# Set Naming on Auth Hook
LEDGER_APP_NAME = clean_setting("LEDGER_APP_NAME", "Ledger")

# Caching Key for Caching System
STORAGE_BASE_KEY = "ledger_storage_"

# zKillboard - https://zkillboard.com/
EVE_BASE_URL = "https://esi.evetech.net/"
EVE_API_URL = "https://esi.evetech.net/latest/"
EVE_BASE_URL_REGEX = r"^http[s]?:\/\/esi.evetech\.net\/"

# fuzzwork
FUZZ_BASE_URL = "https://www.fuzzwork.co.uk/"
FUZZ_API_URL = "https://www.fuzzwork.co.uk/api/"
FUZZ_BASE_URL_REGEX = r"^http[s]?:\/\/(www\.)?fuzzwork\.co\.uk\/"

# If True you need to set up the Logger
LEDGER_LOGGER_USE = clean_setting("LEDGER_LOGGER_USE", False)

# Max Time to set Char Inactive
LEDGER_CHAR_MAX_INACTIVE_DAYS = clean_setting("LEDGER_CHAR_MAX_INACTIVE_DAYS", 3)

# Set the Stale Status for Ledger Updates
LEDGER_STALE_STATUS = clean_setting("LEDGER_STALE_STATUS", 1)

# Set the Corporation Tax for Corporation & CharacterLedger Caluclation of ESS Payout
LEDGER_CORP_TAX = clean_setting("LEDGER_CORP_TAX", 15)

# Global timeout for tasks in seconds to reduce task accumulation during outages.
LEDGER_TASKS_TIME_LIMIT = clean_setting("LEDGER_TASKS_TIME_LIMIT", 7200)
