from datetime import datetime

from ninja import NinjaAPI

from django.shortcuts import render
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter

from ledger.api import schema
from ledger.api.api_helper.information_helper import (
    InformationData,
    InformationProcessAlliance,
    InformationProcessCharacter,
    InformationProcessCorporation,
)
from ledger.api.helpers import (
    get_all_corporations_from_alliance,
    get_character,
    get_corp_alts_queryset,
    get_corporation,
    get_journal_entitys,
)
from ledger.hooks import get_extension_logger
from ledger.models.general import EveEntity

logger = get_extension_logger(__name__)

entity_context = {
    "error_title": "403 Error",
    "error_message": "Entity not found.",
}


def error_context(title, msg):
    return {
        "error_title": title,
        "error_message": msg,
    }


def _character_information(
    request,
    entity_id: int,
    date_obj: datetime,
    view: str,
    current_date: timezone.datetime,
):
    character_id = request.GET.get("character_id", None)

    if character_id is None:
        perms, character = get_character(request, entity_id)
    else:
        perms, character = get_character(request, character_id)

    if perms is False:
        return render(
            request,
            "ledger/modals/information/error.html",
            error_context(
                "Permission Denied", "You don't have permission to view this character"
            ),
            status=403,
        )

    if character_id is None:
        linked_characters = (
            character.character_ownership.user.character_ownerships.select_related(
                "character"
            ).all()
        )

        chars_list = linked_characters.values_list("character__character_id", flat=True)
        linked_char = EveCharacter.objects.filter(
            character_id__in=chars_list,
        )
        character = EveCharacter.objects.get(character_id=entity_id)
    else:
        linked_char = EveCharacter.objects.filter(
            character_id__in=[character_id],
        )

    # Create the Ledger
    ledger_data = InformationData(
        request=request,
        character=character,
        date=date_obj,
        view=view,
        current_date=current_date,
    )

    ledger = InformationProcessCharacter(
        characters=linked_char,
        data=ledger_data,
    )
    context = {
        "character": ledger.character_information_dict(),
        "mode": "TAX",
    }
    return render(
        request,
        "ledger/modals/information/view_character_content.html",
        context,
    )


def _corporation_information(
    request,
    entity_id: int,
    date_obj: datetime,
    view: str,
    current_date: timezone.datetime,
):
    main_character_id = request.GET.get("main_character_id", None)

    perms, corporation = get_corporation(request, entity_id)

    if perms is False:
        return render(
            request,
            "ledger/modals/information/error.html",
            error_context(
                "Permission Denied", "You don't have permission to view this character"
            ),
            status=403,
        )

    if main_character_id is None:
        chars_list = get_journal_entitys(
            date=date_obj, view=view, corporations=[entity_id]
        )
        linked_char = EveEntity.objects.filter(
            eve_id__in=chars_list,
        )
        main_character = None
    else:
        main_character = get_character(request, main_character_id)[1]
        if main_character is None:
            return render(
                request,
                "ledger/modals/information/error.html",
                error_context("Entity not Found", "This Entity does not exist."),
                status=403,
            )

        linked_char = get_corp_alts_queryset(main_character)
        corporation = None

    # Create the Ledger
    ledger_data = InformationData(
        request=request,
        character=main_character,
        corporation=corporation,
        date=date_obj,
        view=view,
        current_date=current_date,
    )

    ledger = InformationProcessCorporation(
        corporation_id=entity_id, character_ids=linked_char, data=ledger_data
    )
    context = {
        "character": ledger.corporation_information_dict(),
        "mode": "TAX",
    }
    return render(
        request,
        "ledger/modals/information/view_character_content.html",
        context,
    )


def _alliance_information(
    request,
    entity_id: int,
    date_obj: datetime,
    view: str,
    current_date: timezone.datetime,
):
    corporation_id = request.GET.get("corporation_id", None)
    main_corp = None

    if corporation_id is None:
        perms, corporations = get_all_corporations_from_alliance(request, entity_id)
    else:
        perms, main_corp = get_corporation(request, corporation_id)
        corporations = [corporation_id]

    if perms is False:
        return render(
            request,
            "ledger/modals/information/error.html",
            error_context(
                "Permission Denied", "You don't have permission to view this character"
            ),
            status=404,
        )

    # Create the Ledger
    ledger_data = InformationData(
        request=request,
        corporation=main_corp,
        date=date_obj,
        view=view,
        current_date=current_date,
    )
    ledger = InformationProcessAlliance(corporations=corporations, data=ledger_data)
    context = {
        "character": ledger.alliance_information_dict(),
        "mode": "TAX",
    }
    return render(
        request,
        "ledger/modals/information/view_character_content.html",
        context,
    )


class LedgerTemplateApiEndpoints:
    tags = ["LedgerInformationDetails"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "{entity_type}/{entity_id}/template/date/{date}/view/{view}/",
            response={200: list[schema.CharacterLedgerTemplate], 403: str},
            tags=self.tags,
        )
        # pylint: disable=too-many-positional-arguments, too-many-locals
        def get_information_modal(
            request,
            entity_type: str,
            entity_id: int,
            date: str,
            view: str,
        ):
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return 403, "Invalid Date format. Use YYYY-MM-DD"

            current_date = timezone.now()

            if entity_type == "character":
                return _character_information(
                    request, entity_id, date_obj, view, current_date
                )
            if entity_type == "corporation":
                return _corporation_information(
                    request, entity_id, date_obj, view, current_date
                )
            if entity_type == "alliance":
                return _alliance_information(
                    request, entity_id, date_obj, view, current_date
                )
            return None
