# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.api import schema
from ledger.api.api_helper.alliance_helper import AllianceProcess
from ledger.api.api_helper.character_helper import CharacterProcess
from ledger.api.api_helper.corporation_helper import (
    CorporationProcess,
)
from ledger.api.helpers import (
    get_alliance,
    get_alts_queryset,
    get_character_or_none,
    get_corporation,
)
from ledger.models.characteraudit import CharacterAudit

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def ledger_api_process(
    request, entity_type: str, entity_id: int, date: timezone.datetime, view: str
):
    singleview = request.GET.get("single", False)
    perm = True
    result = {"perm": None, "process": None}

    if entity_type == "character":
        character_id = request.GET.get("character_id", None)
        perm, character = get_character_or_none(request, entity_id)

        if character is None:
            return None, None

        if character_id is None and singleview is False:
            characters = get_alts_queryset(character)
        elif character_id is None:
            characters = CharacterAudit.objects.filter(
                eve_character__character_id=character.eve_character.character_id,
            )
        else:
            perm, character = get_character_or_none(request, character_id)
            characters = CharacterAudit.objects.filter(
                eve_character__character_id=character_id,
            )

        if character is not None:
            result["perm"] = perm
            result["process"] = CharacterProcess(
                main=character, chars=characters, date=date, view=view
            )

    elif entity_type == "corporation":
        main_character_id = request.GET.get("main_character_id", None)
        perm, corporation = get_corporation(request, entity_id)
        main_character = None

        if corporation is not None:
            if main_character_id:
                main_character = get_character_or_none(request, main_character_id)[1]

            result["perm"] = perm
            result["process"] = CorporationProcess(
                corporation=corporation,
                date=date,
                main_character=main_character,
                view=view,
            )

    elif entity_type == "alliance":
        corporation_id = request.GET.get("corporation_id", None)
        perm, alliance = get_alliance(request, entity_id)
        corporation = None

        if alliance is not None:
            if corporation_id:
                corporation = get_corporation(request, corporation_id)[1]

            result["perm"] = perm
            result["process"] = AllianceProcess(
                alliance=alliance, corporation=corporation, date=date, view=view
            )

    return result["perm"], result["process"]


class LedgerApiEndpoints:
    tags = ["Ledger"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "{entity_type}/{entity_id}/ledger/date/{date}/view/{view}/",
            response={200: schema.Ledger, 403: str, 404: str},
            tags=self.tags,
        )
        def get_ledger(
            request: WSGIRequest, entity_type: str, entity_id: int, date: str, view: str
        ):
            try:
                date_obj = timezone.datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return 403, "Invalid Date format. Use YYYY-MM-DD"

            perm, ledger = ledger_api_process(
                request, entity_type, entity_id, date_obj, view
            )

            if perm is False:
                return 403, str(_("Permission Denied"))
            if perm is None:
                return 404, str(_("Entity Not Found"))

            output = ledger.generate_ledger()
            return output

        @api.get(
            "{entity_type}/{entity_id}/template/date/{date}/view/{view}/",
            response={200: schema.Ledger, 403: str, 404: str},
            tags=self.tags,
        )
        def get_entity_information(
            request: WSGIRequest, entity_type: str, entity_id: int, date: str, view: str
        ):
            try:
                date_obj = timezone.datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return 403, "Invalid Date format. Use YYYY-MM-DD"

            perm, ledger = ledger_api_process(
                request, entity_type, entity_id, date_obj, view
            )

            if perm is False:
                return 403, str(_("Permission Denied"))
            if perm is None:
                return 404, str(_("Entity Not Found"))

            context = {
                "character": ledger.generate_template(),
                "mode": "CHARACTER",
            }
            return render(
                request,
                "ledger/partials/information/view_character_content.html",
                context,
            )
