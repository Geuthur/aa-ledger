"""
App Settings
"""

# Django
from app_utils.app_settings import clean_setting

TESTING_MODE = False
# Set Test Mode True or False

APP_NAME = "Geuthur"

# Killboard

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

# Corporation & Character Audit
# If Character Ledger use Memeberaudit Journal or Own
MEMBERAUDIT_USE = clean_setting("MEMBERAUDIT_USE", False)

# Switch between AA-Corp Stats and CorpStats Two APP
CORPSTATS_TWO = clean_setting("CORPSTATS_TWO", False)

# Max Time to set Char Inactive
CHAR_MAX_INACTIVE_DAYS = clean_setting("CHAR_MAX_INACTIVE_DAYS", 3)

# Set the Corporation Tax for Corporation & CharacterLedger Caluclation of ESS Payout
CORP_TAX = clean_setting("CORP_TAX", 15)
