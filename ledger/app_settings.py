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
LEDGER_TASKS_TIME_LIMIT = clean_setting("LEDGER_TASKS_TIME_LIMIT", 600)

LEDGER_STALE_TYPES = clean_setting(
    "LEDGER_STALE_TYPES",
    {
        "wallet_journal": 30,
        "wallet_division_names": 30,
        "wallet_division": 30,
        "mining_ledger": 30,
        "planets": 30,
        "planets_details": 30,
    },
)

# Mining Price Calculation
LEDGER_USE_COMPRESSED = clean_setting("LEDGER_USE_COMPRESSED", True)
LEDGER_PRICE_PERCENTAGE = clean_setting("LEDGER_PRICE_PERCENTAGE", 0.9)

# Ledger Cache System
LEDGER_CACHE_STALE = 60 * 60 * 168  # 168 hours
LEDGER_CACHE_KEY = "LEDGER"
LEDGER_CACHE_ENABLED = True

# Maximum Number of Objects processed per run of DJANGO Batch Method
# Controls how many database records are inserted in a single batch operation.
# If you encounter "Got a packet bigger than 'max_allowed_packet' bytes" errors,
# reduce this value (e.g., to 250 or 100).
# Can be increased for better performance if your MySQL max_allowed_packet setting
# is configured higher (default is usually 16-64MB).
LEDGER_BULK_BATCH_SIZE = clean_setting("LEDGER_BULK_BATCH_SIZE", 500)
