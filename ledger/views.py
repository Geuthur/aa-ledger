"""Views: the React entry point and the ESI SSO registration of owners."""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.eveonline.providers import open_api_provider
from esi.decorators import token_required

# AA Ledger
from ledger import __app_name__, __version__, tasks
from ledger.models import CharacterOwner, CorporationOwner
from ledger.models.general import EveEntity
from ledger.providers import logger


@login_required
@permission_required("ledger.basic_access")
def react_base(request: WSGIRequest):
    """Serve the React app; routing and permissions of the pages are handled by the API."""
    context = {"version": __version__, "app_name": __app_name__}
    return render(request, "ledger/react_base.html", context=context)


@login_required
@token_required(scopes=CharacterOwner.get_esi_scopes())
@permission_required("ledger.basic_access")
def add_char(request, token):
    char = CharacterOwner.objects.update_or_create(
        eve_character=EveCharacter.objects.get_character_by_id(token.character_id),
        defaults={
            "active": True,
            "character_name": token.character_name,
        },
    )[0]
    tasks.update_character.apply_async(
        kwargs={
            "eve_id": char.eve_character.character_id,
            "force_refresh": True,
            "update_alts": False,
        },
        priority=6,
    )

    msg = _("{character_name} successfully added/updated to Ledger").format(
        character_name=char.eve_character.character_name,
    )
    messages.info(request, msg)
    return redirect("ledger:index")


@login_required
@token_required(scopes=CorporationOwner.get_esi_scopes())
@permission_required(["ledger.manage_access"])
def add_corp(request, token) -> HttpResponse:
    char = get_object_or_404(EveCharacter, character_id=token.character_id)
    eve_corp = EveCorporationInfo.objects.get_or_create(
        corporation_id=char.corporation_id,
        defaults={
            "member_count": 0,
            "corporation_ticker": char.corporation_ticker,
            "corporation_name": char.corporation_name,
        },
    )[0]

    corp = CorporationOwner.objects.update_or_create(
        eve_corporation=eve_corp,
        defaults={
            "corporation_name": eve_corp.corporation_name,
        },
    )[0]

    tasks.update_corporation.apply_async(
        kwargs={"eve_id": corp.eve_corporation.corporation_id, "force_refresh": True},
        priority=6,
    )
    msg = _("{corporation_name} successfully added/updated to Ledger").format(
        corporation_name=corp.corporation_name,
    )
    messages.info(request, msg)
    return redirect(f"{reverse('ledger:index')}corporation/")


@login_required
@token_required(scopes=["publicData"])
@permission_required(["ledger.manage_access"])
def add_ally(request, token) -> HttpResponse:
    char = get_object_or_404(EveCharacter, character_id=token.character_id)
    try:
        ally = EveAllianceInfo.objects.get(alliance_id=char.alliance_id)

        msg = _("{alliance_name} is already in the Ledger System").format(
            alliance_name=ally.alliance_name,
        )
        messages.info(request, msg)
    except EveAllianceInfo.DoesNotExist:
        try:
            ally_data = open_api_provider.get_alliance(char.alliance_id)
            ally, __ = EveAllianceInfo.objects.get_or_create(
                alliance_id=ally_data.id,
                defaults={
                    "alliance_name": ally_data.name,
                    "alliance_ticker": ally_data.ticker,
                    "executor_corp_id": ally_data.executor_corp_id,
                },
            )
            # Add/Update All Corporations AA model
            ally.populate_alliance()

            # Add the alliance to the EveEntity model
            EveEntity.objects.get_or_create(
                eve_id=ally.alliance_id,
                defaults={
                    "name": ally.alliance_name,
                    "category": "alliance",
                },
            )
            msg = _("{alliance_name} successfully added to Ledger").format(
                alliance_name=ally.alliance_name,
            )
            messages.success(request, msg)
        except Exception as exc:  # pylint: disable=broad-except
            msg = _("Failed to fetch Alliance data for {alliance_name}").format(
                alliance_name=char.alliance_name,
            )
            messages.warning(request, msg)
            logger.debug(
                "Error fetching alliance data for alliance_id %s: %s",
                char.alliance_id,
                exc,
            )
            return redirect(f"{reverse('ledger:index')}alliance/")
    return redirect(f"{reverse('ledger:index')}alliance/")
