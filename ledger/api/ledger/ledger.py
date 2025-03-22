from datetime import datetime

from ninja import NinjaAPI

from ledger.api import schema
from ledger.api.api_helper.alliance_helper import AllianceProcess
from ledger.api.api_helper.character_helper import CharacterProcess
from ledger.api.api_helper.corporation_helper import CorporationProcess
from ledger.api.helpers import (
    get_alliance,
    get_alts_queryset,
    get_character,
    get_corporation,
)
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


# pylint: disable=too-many-function-args
def ledger_api_process(request, entity_type: str, entity_id: int, date: str, view: str):
    singleview = request.GET.get("single", False)
    perm = True

    if entity_type == "corporation":
        perm, corporation = get_corporation(request, entity_id)
    if entity_type == "character":
        perm, entitys = get_character(request, entity_id)
    if entity_type == "alliance":
        perm, alliance = get_alliance(request, entity_id)

    if perm is False:
        return "Permission Denied", None

    if perm is None:
        return None, None

    if entity_type == "character":
        if not singleview:
            characters = get_alts_queryset(entitys)
        else:
            characters = [entitys]
        return CharacterProcess(characters, date, view)

    if entity_type == "corporation":
        return CorporationProcess(corporation, date, view)

    if entity_type == "alliance":
        return AllianceProcess(alliance, date, view)

    return "Wrong Entity Type"


class LedgerApiEndpoints:
    tags = ["Ledger"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "{entity_type}/{entity_id}/ledger/date/{date}/view/{view}/",
            response={200: list[schema.Ledger], 403: str, 404: str},
            tags=self.tags,
        )
        def get_ledger(request, entity_type: str, entity_id: int, date: str, view: str):
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return 403, "Invalid Date format. Use YYYY-MM-DD"

            ledger = ledger_api_process(request, entity_type, entity_id, date_obj, view)

            if isinstance(ledger, str):
                return 403, ledger

            if ledger is None:
                return 404, "No data found"

            output = ledger.generate_ledger()
            return output
