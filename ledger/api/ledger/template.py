from datetime import datetime

from ninja import NinjaAPI

from django.shortcuts import render
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter

from ledger.api import schema
from ledger.api.api_helper.template_helper import TemplateData, TemplateProcess
from ledger.api.helpers import (
    get_alliance,
    get_alts_queryset,
    get_character,
    get_corp_alts_queryset,
    get_corporation,
    get_journal_entitys,
    get_main_and_alts_ids_corporations,
)
from ledger.hooks import get_extension_logger
from ledger.models import CorporationAudit
from ledger.models.general import EveEntity

logger = get_extension_logger(__name__)


def ledger_api_process(request, entity_type: str, entity_id: int):
    perm = None
    if entity_type == "corporation":
        perm, entitys = get_corporation(request, entity_id)

    if entity_type == "alliance":
        perm, entitys = get_alliance(request, entity_id)
        # Get all corporations in the alliance
        entitys = CorporationAudit.objects.filter(
            corporation__alliance__alliance_id__in=entitys
        ).values_list("corporation__corporation_id", flat=True)

    return perm, entitys


class LedgerTemplateApiEndpoints:
    tags = ["LedgerInformationDetails"]

    def __init__(self, api: NinjaAPI):

        @api.get(
            "character/{character_id}/template/date/{date}/view/{view}/",
            response={200: list[schema.CharacterLedgerTemplate], 403: str},
            tags=self.tags,
        )
        def get_ledger_char_details_information(
            request, character_id: int, date: str, view: str
        ):
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return 403, "Invalid Date format. Use YYYY-MM-DD"

            request_overall = request.GET.get("overall", False)
            perms, main = get_character(request, character_id)
            entitys = get_main_and_alts_ids_corporations(request)

            if not perms:
                context = {
                    "error_title": "Permission Denied",
                    "error_message": "You don't have permission to view this character's ledger.",
                }
                return render(
                    request, "ledger/modals/information/error.html", context, status=403
                )

            alts = get_alts_queryset(main)
            chars_list = [char.character_id for char in alts]

            overall_mode = character_id == 0 or request_overall
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
                return render(
                    request, "ledger/modals/information/error.html", context, status=403
                )

            # Create the Ledger
            ledger_data = TemplateData(
                request=request,
                main=main,
                date=date_obj,
                view=view,
                corporations_ids=entitys,
                current_date=current_date,
            )
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

        @api.get(
            "{entity_type}/{entity_id}/{main_id}/template/date/{date}/view/{view}/",
            response={200: list[schema.CharacterLedgerTemplate], 403: str},
            tags=self.tags,
        )
        # pylint: disable=too-many-positional-arguments, too-many-locals
        def get_ledger_corp_ally_details_information(
            request,
            entity_type: str,
            entity_id: int,
            main_id: int,
            date: str,
            view: str,
            corp: bool = False,
        ):
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return 403, "Invalid Date format. Use YYYY-MM-DD"

            perm, entitys = ledger_api_process(request, entity_type, entity_id)
            corp_view = False

            if not perm:
                context = {
                    "error_title": "Permission Denied",
                    "error_message": "You don't have permission to view this corporation's ledger.",
                }
                return render(
                    request, "ledger/modals/information/error.html", context, status=403
                )

            current_date = timezone.now()

            if entity_id == main_id:
                corp_view = True

            _, char = get_character(request, main_id, corp=corp_view)

            if char is None:
                context = {
                    "error_title": "403 Error",
                    "error_message": "Entity not found.",
                }
                return render(
                    request, "ledger/modals/information/error.html", context, status=403
                )

            overall_mode = main_id == 0

            if overall_mode:
                chars_list = get_journal_entitys(
                    date=date_obj, view=view, corporations=entitys
                )
                linked_char = EveEntity.objects.filter(
                    eve_id__in=chars_list,
                )
            elif corp:
                linked_char = EveEntity.objects.filter(
                    eve_id__in=[main_id],
                )
                overall_mode = True
            else:
                linked_char = get_corp_alts_queryset(char, corporations=None)

            # Create the Ledger
            ledger_data = TemplateData(
                request=request,
                main=char,
                date=date_obj,
                view=view,
                corporations_ids=entitys,
                current_date=current_date,
            )
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
