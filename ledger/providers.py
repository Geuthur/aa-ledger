"""Shared ESI client for Voices of War."""

from esi.clients import EsiClientProvider

from ledger import __title__, __version__

esi = EsiClientProvider(app_info_text=f"{__title__} v{__version__}")
