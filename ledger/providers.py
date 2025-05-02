"""Shared ESI client for Voices of War."""

# Alliance Auth
from esi.clients import EsiClientProvider

# AA Ledger
from ledger import __title__, __version__

esi = EsiClientProvider(app_info_text=f"{__title__} v{__version__}")
