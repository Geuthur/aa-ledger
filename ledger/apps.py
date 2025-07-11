"""App Configuration"""

# Django
from django.apps import AppConfig

# AA Ledger
from ledger import __version__


class LedgerConfig(AppConfig):
    """App Config"""

    default_auto_field = "django.db.models.AutoField"
    name = "ledger"
    label = "ledger"
    verbose_name = f"Ledger v{__version__}"
