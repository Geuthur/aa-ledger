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
        "wallet_journal": 60,
        "wallet_division_names": 60,
        "wallet_division": 60,
        "mining_ledger": 10,
        "planets": 10,
        "planets_details": 10,
    },
)

# Mining Price Calculation
LEDGER_USE_COMPRESSED = getattr(settings, "LEDGER_USE_COMPRESSED", True)
LEDGER_PRICE_PERCENTAGE = getattr(settings, "LEDGER_PRICE_PERCENTAGE", 0.9)

# Maximum Number of Objects processed per run of DJANGO Batch Method
# Controls how many database records are inserted in a single batch operation.
# If you encounter "Got a packet bigger than 'max_allowed_packet' bytes" errors,
# reduce this value (e.g., to 250 or 100).
# Can be increased for better performance if your MySQL max_allowed_packet setting
# is configured higher (default is usually 16-64MB).
LEDGER_BULK_BATCH_SIZE = getattr(settings, "LEDGER_BULK_BATCH_SIZE", 500)

# Cooldown in seconds between manual character updates triggered from the frontend
LEDGER_MANUAL_UPDATE_COOLDOWN = getattr(settings, "LEDGER_MANUAL_UPDATE_COOLDOWN", 300)
