"""
App Settings
"""

# Django
from django.conf import settings

# Set Naming on Auth Hook
LEDGER_APP_NAME = getattr(settings, "LEDGER_APP_NAME", "Ledger")

# Global timeout for tasks in seconds to reduce task accumulation during outages.
LEDGER_TASKS_TIME_LIMIT = getattr(settings, "LEDGER_TASKS_TIME_LIMIT", 600)

LEDGER_STALE_TYPES = getattr(
    settings,
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
LEDGER_USE_COMPRESSED = getattr(settings, "LEDGER_USE_COMPRESSED", True)
LEDGER_PRICE_PERCENTAGE = getattr(settings, "LEDGER_PRICE_PERCENTAGE", 0.9)

# Ledger Cache System
LEDGER_CACHE_STALE = 60 * 60 * 168  # 168 hours
LEDGER_CACHE_KEY = "LEDGER"
LEDGER_CACHE_ENABLED = getattr(settings, "LEDGER_CACHE_ENABLED", True)

# Maximum Number of Objects processed per run of DJANGO Batch Method
# Controls how many database records are inserted in a single batch operation.
# If you encounter "Got a packet bigger than 'max_allowed_packet' bytes" errors,
# reduce this value (e.g., to 250 or 100).
# Can be increased for better performance if your MySQL max_allowed_packet setting
# is configured higher (default is usually 16-64MB).
LEDGER_BULK_BATCH_SIZE = getattr(settings, "LEDGER_BULK_BATCH_SIZE", 500)
