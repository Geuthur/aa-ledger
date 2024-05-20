"""App Configuration"""

# Django
from django.apps import AppConfig

# AA Example App
from ledger import __version__


class LedgerConfig(AppConfig):
    """App Config"""

    default_auto_field = "django.db.models.AutoField"
    author = "Geuthur"
    name = "ledger"
    label = "ledger"
    verbose_name = f"Ledger v{__version__}"
