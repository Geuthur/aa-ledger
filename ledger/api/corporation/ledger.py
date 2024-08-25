from typing import List

from ninja import NinjaAPI

from ledger.api import schema
from ledger.api.helpers import get_corporation, get_main_and_alts_corporations
from ledger.api.managers.corporation_manager import CorporationProcess
from ledger.hooks import get_extension_logger
from ledger.models import CorporationAudit

logger = get_extension_logger(__name__)


class LedgerApiEndpoints:
    tags = ["CorporationLedger"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/ledger/year/{year}/month/{month}/",
            response={200: List[schema.Ledger], 403: str},
            tags=self.tags,
        )
        def get_corporation_ledger(request, corporation_id: int, year: int, month: int):
            response, _ = get_corporation(request, corporation_id)

            if not response:
                return 403, "Permission Denied"

            # pylint: disable=duplicate-code
            if corporation_id == 0:
                corporations = get_main_and_alts_corporations(request)
            else:
                corporations = [corporation_id]

            ledger = CorporationProcess(year, month, corporations)
            output = ledger.generate_ledger()

            return output

        @api.get(
            "corporation/{corporation_id}/billboard/year/{year}/month/{month}/",
            response={200: List[schema.Billboard], 403: str},
            tags=self.tags,
        )
        def get_billboard_ledger(request, corporation_id: int, year: int, month: int):
            response, _ = get_corporation(request, corporation_id)

            if not response:
                return 403, "Permission Denied"

            # pylint: disable=duplicate-code
            if corporation_id == 0:
                corporations = get_main_and_alts_corporations(request)
            else:
                corporations = [corporation_id]

            ledger = CorporationProcess(year, month, corporations)
            output = ledger.generate_billboard(corporations)

            return output

        @api.get(
            "corporation/ledger/admin/",
            response={200: List[schema.CorporationAdmin], 403: str},
            tags=self.tags,
        )
        def get_corporation_admin(request):
            corporations = CorporationAudit.objects.visible_to(request.user)

            if not corporations:
                return 403, "Permission Denied"

            corporation_dict = {}

            for corporation in corporations:
                # pylint: disable=broad-exception-caught
                try:
                    corporation_dict[corporation.corporation.corporation_id] = {
                        "corporation_id": corporation.corporation.corporation_id,
                        "corporation_name": corporation.corporation.corporation_name,
                    }
                except Exception:
                    continue

            output = []
            output.append({"corporation": corporation_dict})

            return output
