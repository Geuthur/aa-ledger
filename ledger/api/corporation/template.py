from ninja import NinjaAPI

from django.shortcuts import render
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter

from ledger.api import schema
from ledger.api.helpers import (
    get_alts_queryset,
    get_character,
    get_corporation,
    get_main_and_alts_ids_all,
)
from ledger.api.managers.template_manager import TemplateData, TemplateProcess
from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import CorporationWalletJournalEntry

logger = get_extension_logger(__name__)


# pylint: disable=too-many-locals
class LedgerTemplateApiEndpoints:
    tags = ["CorporationLedgerTemplate"]

    def __init__(self, api: NinjaAPI):

        @api.get(
            "corporation/{corporation_id}/character/{main_id}/ledger/template/year/{year}/month/{month}/",
            response={200: list[schema.CharacterLedgerTemplate], 403: str},
            tags=self.tags,
        )
        # pylint: disable=too-many-positional-arguments
        def get_corporation_ledger_template(
            request,
            corporation_id: int,
            main_id: int,
            year: int,
            month: int,
            corp: bool = False,
        ):
            response, corporations = get_corporation(request, corporation_id)

            if response is False:
                return 403, "Permission Denied"

            current_date = timezone.now()

            _, char = get_character(request, main_id)

            # Get all Chars from the main (including the main char itself)
            alts = get_alts_queryset(char, corporations=corporations)
            linked_char = list(alts)

            overall_mode = main_id == 0

            if overall_mode:
                second_party_ids = CorporationWalletJournalEntry.objects.filter(
                    division__corporation__corporation__corporation_id__in=corporations,
                ).values_list("second_party_id", flat=True)

                chars_list = get_main_and_alts_ids_all(corporations)
                combined_list = list(set(chars_list) | set(second_party_ids))

                linked_char = EveCharacter.objects.filter(
                    character_id__in=combined_list,
                )

            elif corp:
                linked_char = EveCharacter.objects.filter(
                    corporation_id__in=[main_id],
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
