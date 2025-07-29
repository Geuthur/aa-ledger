"""
App Settings
"""

# Standard Library
import sys

# Alliance Auth (External Libs)
from app_utils.app_settings import clean_setting

IS_TESTING = sys.argv[1:2] == ["test"]

# Set Test Mode True or False

# Set Naming on Auth Hook
LEDGER_APP_NAME = clean_setting("LEDGER_APP_NAME", "Ledger")

# zKillboard - https://zkillboard.com/
EVE_BASE_URL = "https://esi.evetech.net/"
EVE_API_URL = "https://esi.evetech.net/latest/"
EVE_BASE_URL_REGEX = r"^http[s]?:\/\/esi.evetech\.net\/"

# fuzzwork
FUZZ_BASE_URL = "https://www.fuzzwork.co.uk/"
FUZZ_API_URL = "https://www.fuzzwork.co.uk/api/"
FUZZ_BASE_URL_REGEX = r"^http[s]?:\/\/(www\.)?fuzzwork\.co\.uk\/"

# Global timeout for tasks in seconds to reduce task accumulation during outages.
LEDGER_TASKS_TIME_LIMIT = clean_setting("LEDGER_TASKS_TIME_LIMIT", 7200)

LEDGER_STALE_TYPES = {
    "wallet_journal": 30,
    "wallet_division_names": 30,
    "wallet_division": 30,
    "mining_ledger": 30,
    "planets": 30,
    "planets_details": 30,
}
