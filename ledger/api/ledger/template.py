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
    get_corporation,
    get_main_and_alts_ids_all,
    get_main_and_alts_ids_corporations,
)
from ledger.hooks import get_extension_logger
from ledger.models import CorporationAudit

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
            "character/{character_id}/template/year/{year}/month/{month}/",
            response={200: list[schema.CharacterLedgerTemplate], 403: str},
            tags=self.tags,
        )
        def get_ledger_char_details_information(
            request, character_id: int, year: int, month: int
        ):
            request_main = request.GET.get("main", False)
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
                return render(
                    request, "ledger/modals/information/error.html", context, status=403
                )

            # Create the Ledger
            ledger_data = TemplateData(
                request=request,
                main=main,
                year=year,
                month=month,
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
            "{entity_type}/{entity_id}/{main_id}/template/year/{year}/month/{month}/",
            response={200: list[schema.CharacterLedgerTemplate], 403: str},
            tags=self.tags,
        )
        # pylint: disable=too-many-positional-arguments, too-many-locals
        def get_ledger_corp_ally_details_information(
            request,
            entity_type: str,
            entity_id: int,
            main_id: int,
            year: int,
            month: int,
            corp: bool = False,
        ):
            perm, entitys = ledger_api_process(request, entity_type, entity_id)
            corp_template = False

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
                corp_template = True

            _, char = get_character(request, main_id, corp=corp_template)

            if char is None:
                context = {
                    "error_title": "403 Error",
                    "error_message": "Character not found.",
                }
                return render(
                    request, "ledger/modals/information/error.html", context, status=403
                )

            # Get all Chars from the main (including the main char itself)
            alts = get_alts_queryset(char, corporations=entitys)
            linked_char = list(alts)

            overall_mode = main_id == 0

            if overall_mode:
                chars_list = get_main_and_alts_ids_all(entitys)
                linked_char = EveCharacter.objects.filter(
                    character_id__in=chars_list,
                )
            elif corp:
                if entity_type == "corporation":
                    linked_char = EveCharacter.objects.filter(
                        corporation_id__in=[main_id],
                    )
                else:
                    linked_char = EveCharacter.objects.filter(
                        alliance_id__in=[main_id],
                    )
                overall_mode = True

            # Create the Ledger

            ledger_data = TemplateData(
                request=request,
                main=char,
                year=year,
                month=month,
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
