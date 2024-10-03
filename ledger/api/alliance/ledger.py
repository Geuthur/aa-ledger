from ninja import NinjaAPI

from ledger.api import schema
from ledger.api.helpers import get_alliance
from ledger.api.managers.corporation_manager import CorporationProcess
from ledger.hooks import get_extension_logger
from ledger.models import CorporationAudit

logger = get_extension_logger(__name__)


class LedgerApiEndpoints:
    tags = ["CorporationLedger"]

    # pylint: disable=duplicate-code
    def __init__(self, api: NinjaAPI):
        @api.get(
            "alliance/{alliance_id}/ledger/year/{year}/month/{month}/",
            response={200: list[schema.Ledger], 403: str},
            tags=self.tags,
        )
        def get_alliance_ledger(request, alliance_id: int, year: int, month: int):
            response, alliances = get_alliance(request, alliance_id)

            if response is False:
                return 403, "Permission Denied"

            # Get all corporations in the alliance
            corporations = CorporationAudit.objects.filter(
                corporation__alliance__alliance_id__in=alliances
            ).values_list("corporation__corporation_id", flat=True)

            ledger = CorporationProcess(year, month, corporations)
            output = ledger.generate_ledger()

            return output

        @api.get(
            "alliance/{alliance_id}/billboard/year/{year}/month/{month}/",
            response={200: list[schema.Billboard], 403: str},
            tags=self.tags,
        )
        def get_billboard_ledger(request, alliance_id: int, year: int, month: int):
            response, alliances = get_alliance(request, alliance_id)

            if response is False:
                return 403, "Permission Denied"

            # Get all corporations in the alliance
            corporations = CorporationAudit.objects.filter(
                corporation__alliance__alliance_id__in=alliances
            ).values_list("corporation__corporation_id", flat=True)

            ledger = CorporationProcess(year, month, corporations)
            output = ledger.generate_billboard(corporations)

            return output

        @api.get(
            "alliance/ledger/admin/",
            response={200: list[schema.AllianceAdmin], 403: str},
            tags=self.tags,
        )
        def get_alliance_admin(request):
            corporations = CorporationAudit.objects.visible_to(request.user)

            if corporations is None:
                return 403, "Permission Denied"

            alliance_dict = {}

            for corporation in corporations:
                # pylint: disable=broad-exception-caught
                try:
                    logger.debug(corporation)
                    alliance_dict[corporation.corporation.alliance.alliance_id] = {
                        "alliance_id": corporation.corporation.alliance.alliance_id,
                        "alliance_name": corporation.corporation.alliance.alliance_name,
                    }
                    logger.debug(alliance_dict)
                except Exception:
                    continue
            logger.debug(alliance_dict)
            output = []
            output.append({"alliance": alliance_dict})

            return output
