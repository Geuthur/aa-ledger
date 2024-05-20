from typing import List

from ninja import NinjaAPI

from django.shortcuts import render

from ledger.api import schema
from ledger.api.helpers import get_corporations
from ledger.api.templatemanager import TemplateData, TemplateProcess
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


# TODO Refactor this class
# pylint: disable=too-many-locals, too-many-branches, too-many-statements
class LedgerTemplateApiEndpoints:
    tags = ["CorporationLedgerTemplate"]

    def __init__(self, api: NinjaAPI):

        @api.get(
            "corporation/{main_id}/ledger/template/year/{year}/month/{month}/",
            response={200: List[schema.CharacterLedgerTemplate], 403: str},
            tags=self.tags,
        )
        def get_corporation_ledger_template(
            request, main_id: int, year: int, month: int
        ):
            perms = request.user.has_perm("ledger.basic_access")

            overall_mode = main_id == 0

            if not perms:
                logger.error(
                    "Permission Denied for %s to view corporation ledger template!",
                    request.user,
                )
                return 403, "Permission Denied!"

            character_id = request.user.profile.main_character.character_id
            corporations = get_corporations(request, character_id)

            # Create the Ledger
            ledger_data = TemplateData(request, main_id, year, month)
            ledger = TemplateProcess(corporations, ledger_data, overall_mode)
            context = {"character": ledger.corporation_template()}

            return render(
                request, "ledger/modals/pve/view_character_content.html", context
            )
