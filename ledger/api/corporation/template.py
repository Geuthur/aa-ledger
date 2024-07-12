from typing import List

from ninja import NinjaAPI

from django.shortcuts import render

from allianceauth.eveonline.models import EveCharacter

from ledger.api import schema
from ledger.api.helpers import (
    get_alts_queryset,
    get_character,
    get_main_and_alts_all,
    get_main_and_alts_corporations,
)
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
            perms, char = get_character(request, main_id)

            overall_mode = main_id == 0

            if not perms:
                return 403, "Permission Denied"

            # Get all Chars from the main (including the main char itself)
            alts = get_alts_queryset(char)
            linked_char = list(alts)

            if overall_mode:
                corporations = get_main_and_alts_corporations(request)
                _, chars_list = get_main_and_alts_all(corporations)
                linked_char = EveCharacter.objects.filter(
                    character_id__in=chars_list,
                )
            elif corp:
                linked_char = EveCharacter.objects.filter(
                    corporation_id__in=[main_id],
                )
                overall_mode = True

            # Create the Ledger
            ledger_data = TemplateData(request, main_id, char, year, month)
            ledger = TemplateProcess(linked_char, ledger_data, overall_mode)
            context = {"character": ledger.corporation_template()}

            return render(
                request, "ledger/modals/pve/view_character_content.html", context
            )
