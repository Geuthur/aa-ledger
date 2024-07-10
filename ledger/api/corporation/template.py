from typing import List

from ninja import NinjaAPI

from django.shortcuts import render

from allianceauth.eveonline.models import EveCharacter

from ledger.api import schema
from ledger.api.helpers import get_main_and_alts_corporations
from ledger.api.managers.template_manager import TemplateData, TemplateProcess
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


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
            request, main_id: int, year: int, month: int, corp: bool = False
        ):
            perms = request.user.has_perm("ledger.basic_access")

            overall_mode = main_id == 0

            if not perms:
                return 403, "Permission Denied"

            corporations = get_main_and_alts_corporations(request)

            if overall_mode:
                linked_char = EveCharacter.objects.filter(
                    corporation_id__in=corporations,
                )
            elif corp:
                linked_char = EveCharacter.objects.filter(
                    corporation_id__in=[main_id],
                )
                overall_mode = True
            else:
                linked_char = [
                    EveCharacter.objects.get(
                        character_id=main_id,
                    )
                ]

            # Create the Ledger
            ledger_data = TemplateData(request, main_id, year, month)
            ledger = TemplateProcess(linked_char, ledger_data, overall_mode)
            context = {"character": ledger.corporation_template()}

            return render(
                request, "ledger/modals/pve/view_character_content.html", context
            )
