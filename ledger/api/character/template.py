from typing import List

from ninja import NinjaAPI

from django.shortcuts import render

from allianceauth.eveonline.models import EveCharacter

from ledger.api import schema
from ledger.api.helpers import get_alts_queryset, get_main_character
from ledger.api.templatemanager import TemplateData, TemplateProcess
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


# TODO Refactor this class
# pylint: disable=too-many-locals, too-many-branches, too-many-statements
class LedgerTemplateApiEndpoints:
    tags = ["CharacerLedgerTemplate"]

    def __init__(self, api: NinjaAPI):

        @api.get(
            "account/{character_id}/ledger/template/year/{year}/month/{month}/",
            response={200: List[schema.CharacterLedgerTemplate], 403: str},
            tags=self.tags,
        )
        def get_character_ledger_template(
            request, character_id: int, year: int, month: int
        ):
            overall_mode = character_id == 0
            # Set the character_id to the main character if the character_id is 0
            character_id = (
                request.user.profile.main_character.character_id
                if character_id == 0
                else character_id
            )

            response, main = get_main_character(request, character_id)
            alts = get_alts_queryset(main)

            chars_list = [char.character_id for char in alts]

            if not response:
                return 403, "Permission Denied"

            if overall_mode:
                linked_char = EveCharacter.objects.filter(
                    character_ownership__user=request.user,
                    character_id__in=chars_list,
                )
            else:
                linked_char = [
                    EveCharacter.objects.get(
                        character_ownership__user=request.user,
                        character_id=character_id,
                    )
                ]
            logger.debug(linked_char)

            # Create the Ledger
            ledger_data = TemplateData(request, character_id, year, month)
            ledger = TemplateProcess(linked_char, ledger_data, overall_mode)
            context = {"character": ledger.character_template()}

            return render(
                request, "ledger/modals/pve/view_character_content.html", context
            )
