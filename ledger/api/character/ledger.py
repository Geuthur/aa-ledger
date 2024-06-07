from typing import List

from ninja import NinjaAPI
from ninja.pagination import paginate

from ledger.api import schema
from ledger.api.helpers import Paginator, get_alts_queryset, get_main_character
from ledger.api.managers.ledger_manager import JournalProcess
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class LedgerApiEndpoints:
    tags = ["CharacerLedger"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "account/{character_id}/ledger/year/{year}/month/{month}/",
            response={200: List[schema.CharacterLedger], 403: str},
            tags=self.tags,
        )
        @paginate(Paginator)
        def get_character_ledger(request, character_id: int, year: int, month: int):
            if character_id == 0:
                character_id = request.user.profile.main_character.character_id
            response, main = get_main_character(request, character_id)

            if not response:
                return 403, "Permission Denied"

            characters = get_alts_queryset(main)

            # Create the Ledger
            ledger = JournalProcess(characters, year, month)
            output = ledger.character_ledger()

            return output
