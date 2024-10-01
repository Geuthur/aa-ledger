from ninja import NinjaAPI

from django.shortcuts import render
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter

from ledger.api import schema
from ledger.api.helpers import get_alts_queryset, get_character
from ledger.api.managers.template_manager import TemplateData, TemplateProcess
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class LedgerTemplateApiEndpoints:
    tags = ["CharacerLedgerTemplate"]

    def __init__(self, api: NinjaAPI):

        @api.get(
            "account/{character_id}/ledger/template/year/{year}/month/{month}/",
            response={200: list[schema.CharacterLedgerTemplate], 403: str},
            tags=self.tags,
        )
        def get_character_ledger_template(
            request, character_id: int, year: int, month: int
        ):
            request_main = request.GET.get("main", False)
            perms, main = get_character(request, character_id)
            if not perms:
                context = {
                    "error_title": "Permission Denied",
                    "error_message": "You don't have permission to view this character's ledger.",
                }
                return render(request, "ledger/modals/information/error.html", context)

            alts = get_alts_queryset(main)
            chars_list = [char.character_id for char in alts]

            overall_mode = character_id == 0 or request_main
            current_date = timezone.now()

            try:
                if overall_mode:
                    linked_char = EveCharacter.objects.filter(
                        character_id__in=chars_list,
                    )
                else:
                    linked_char = [
                        EveCharacter.objects.get(
                            character_id=character_id,
                        )
                    ]
            except EveCharacter.DoesNotExist:
                context = {
                    "error_title": "403 Error",
                    "error_message": "Character not found.",
                }
                return render(request, "ledger/modals/information/error.html", context)

            # Create the Ledger
            ledger_data = TemplateData(request, main, year, month, current_date)
            ledger = TemplateProcess(linked_char, ledger_data, overall_mode)
            context = {
                "character": ledger.character_template(),
                "mode": "Ratting",
            }

            return render(
                request,
                "ledger/modals/information/view_character_content.html",
                context,
            )
