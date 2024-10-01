from ninja import NinjaAPI

from django.shortcuts import render
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter

from ledger.api import schema
from ledger.api.helpers import (
    get_alliance,
    get_alts_queryset,
    get_character,
    get_main_and_alts_ids_all,
)
from ledger.api.managers.template_manager import TemplateData, TemplateProcess
from ledger.hooks import get_extension_logger
from ledger.models import CorporationAudit

logger = get_extension_logger(__name__)


# pylint: disable=too-many-locals
class LedgerTemplateApiEndpoints:
    tags = ["CorporationLedgerTemplate"]

    # pylint: disable=duplicate-code
    def __init__(self, api: NinjaAPI):

        @api.get(
            "alliance/{alliance_id}/character/{main_id}/ledger/template/year/{year}/month/{month}/",
            response={200: list[schema.CharacterLedgerTemplate], 403: str},
            tags=self.tags,
        )
        # pylint: disable=too-many-positional-arguments
        def get_alliance_ledger_template(
            request,
            alliance_id: int,
            main_id: int,
            year: int,
            month: int,
            corp: bool = False,
        ):
            response, alliances = get_alliance(request, alliance_id)

            if response is False:
                return 403, "Permission Denied"

            current_date = timezone.now()

            # Get all corporations in the alliance
            corporations = CorporationAudit.objects.filter(
                corporation__alliance__alliance_id__in=alliances
            ).values_list("corporation__corporation_id", flat=True)

            _, char = get_character(request, main_id)

            # Get all Chars from the main (including the main char itself)
            alts = get_alts_queryset(char, corporations=corporations)
            linked_char = list(alts)

            overall_mode = main_id == 0

            if overall_mode:
                chars_list = get_main_and_alts_ids_all(corporations)
                linked_char = EveCharacter.objects.filter(
                    character_id__in=chars_list,
                )
            elif corp:
                linked_char = EveCharacter.objects.filter(
                    alliance_id__in=[main_id],
                )
                overall_mode = True

            # Create the Ledger

            ledger_data = TemplateData(request, char, year, month, current_date)
            ledger = TemplateProcess(linked_char, ledger_data, overall_mode)
            context = {
                "character": ledger.corporation_template(),
                "mode": "TAX",
            }

            return render(
                request,
                "ledger/modals/information/view_character_content.html",
                context,
            )
