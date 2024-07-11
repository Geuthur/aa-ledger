from typing import List

from ninja import NinjaAPI

from ledger.api import schema
from ledger.api.helpers import (
    get_corporation,
    get_main_and_alts_all,
    get_main_and_alts_corporations,
)
from ledger.api.managers.ledger_manager import JournalProcess
from ledger.hooks import get_extension_logger
from ledger.models import CorporationAudit

logger = get_extension_logger(__name__)


class LedgerApiEndpoints:
    tags = ["CorporationLedger"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/ledger/year/{year}/month/{month}/",
            response={200: List[schema.CorporationLedger], 403: str},
            tags=self.tags,
        )
        def get_corporation_ledger(request, corporation_id: int, year: int, month: int):
            response, _ = get_corporation(request, corporation_id)

            if not response:
                return 403, "Permission Denied"

            if corporation_id == 0:
                corporations = get_main_and_alts_corporations(request)
            else:
                corporations = [corporation_id]

            # Create the Ledger
            characters, chars_list = get_main_and_alts_all(corporations)

            chars_mains_test = []
            for _, data in characters.items():
                main = data["main"]
                alts = data["alts"]
                for alt in alts:
                    chars_mains_test.append(alt.character_id)

                chars_mains_test.append(main.character_id)

            ledger = JournalProcess(characters, year, month)
            output = ledger.corporation_ledger(chars_list)

            return output

        @api.get(
            "corporation/ledger/admin/",
            response={200: List[schema.CorporationAdmin], 403: str},
            tags=self.tags,
        )
        def get_corporation_admin(request):
            if request.user.has_perm("ledger.admin_access"):
                corporations = CorporationAudit.objects.visible_to(request.user)
            else:
                return 403, "Permission Denied"

            corporation_dict = {}

            for corporation in corporations:
                # pylint: disable=broad-exception-caught
                try:
                    corporation_dict[corporation.corporation.corporation_id] = {
                        "corporation_id": corporation.corporation.corporation_id,
                        "corporation_name": corporation.corporation.corporation_name,
                    }
                except Exception as e:
                    logger.debug(e)
                    continue

            output = []
            output.append({"corporation": corporation_dict})

            return output
