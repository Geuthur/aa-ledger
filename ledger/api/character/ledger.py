from typing import List

from ninja import NinjaAPI

from ledger.api import schema
from ledger.api.helpers import get_alts_queryset, get_character
from ledger.api.managers.ledger_manager import JournalProcess
from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import CharacterAudit

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
            perm, main = get_character(request, character_id)

            if not perm:
                return 403, "Permission Denied"

            # Create the Ledger
            if character_id == 0:
                characters = get_alts_queryset(main)
            else:
                characters = [main]

            ledger = JournalProcess(characters, year, month)
            output = ledger.character_ledger()

            return output

        @api.get(
            "account/ledger/admin/",
            response={200: List[schema.CharacterAdmin], 403: str},
            tags=self.tags,
        )
        def get_character_admin(request):
            characters = CharacterAudit.objects.visible_eve_characters(request.user)

            if not characters.exists():
                return 403, "Permission Denied"

            character_dict = {}

            for character in characters:
                # pylint: disable=broad-exception-caught
                try:
                    character_dict[character.character_id] = {
                        "character_id": character.character_id,
                        "character_name": character.character_name,
                        "corporation_id": character.corporation_id,
                        "corporation_name": character.corporation.corporation_name,
                    }
                except Exception:
                    continue

            output = []
            output.append({"character": character_dict})

            return output
