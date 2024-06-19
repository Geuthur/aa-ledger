from typing import List

from ninja import NinjaAPI

from ledger.api import schema
from ledger.api.helpers import get_alts_queryset, get_main_character
from ledger.api.managers.ledger_manager import JournalProcess
from ledger.app_settings import IS_TESTING
from ledger.hooks import get_extension_logger
from ledger.view_helpers.core import _storage_key, get_cache_stale, set_cache

logger = get_extension_logger(__name__)


# pylint: disable=duplicate-code
class LedgerApiEndpoints:
    tags = ["CharacerLedger"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "account/{character_id}/ledger/year/{year}/month/{month}/",
            response={200: List[schema.CharacterLedger], 403: str},
            tags=self.tags,
        )
        def get_character_ledger(request, character_id: int, year: int, month: int):
            if character_id == 0:
                character_id = request.user.profile.main_character.character_id
            response, main = get_main_character(request, character_id)

            if not response:
                return 403, "Permission Denied"

            characters = get_alts_queryset(main)

            # Create the Ledger
            output = get_cache_stale(
                _storage_key(f"character_ledger_{character_id}_{year}_{month}")
            )

            if not output:
                ledger = JournalProcess(characters, year, month)
                output = ledger.character_ledger()
                if not IS_TESTING:
                    set_cache(
                        output,
                        _storage_key(f"character_ledger_{character_id}_{year}_{month}"),
                        1,
                    )

            return output
