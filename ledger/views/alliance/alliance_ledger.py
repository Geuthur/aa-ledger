"""PvE Views"""

# Standard Library
import json

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.api.helpers import get_all_corporations_from_alliance, get_alliance
from ledger.helpers.alliance import AllianceData
from ledger.helpers.core import LedgerEntity, add_info_to_context
from ledger.models.corporationaudit import CorporationWalletJournalEntry

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@permission_required("ledger.advanced_access")
def alliance_ledger_index(request):
    """Alliance Ledger Index View"""
    context = {}
    context = add_info_to_context(request, context)
    alliance_id = request.user.profile.main_character.alliance_id
    if not alliance_id:
        alliance_id = 0

    return redirect("ledger:alliance_ledger", alliance_id=alliance_id)


@login_required
@permission_required("ledger.advanced_access")
def alliance_ledger(request, alliance_id, year=None, month=None, day=None):
    """
    Alliance Ledger
    """
    perms, alliance = get_alliance(request, alliance_id)

    context = {
        "title": "Alliance Ledger",
        "alliance_id": alliance_id,
        "disabled": True,
    }

    # pylint: disable=duplicate-code
    if perms is False:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return render(
            request, "ledger/allyledger/alliance_ledger.html", context=context
        )
    # pylint: disable=duplicate-code
    if perms is None:
        msg = _("Alliance not found.")
        messages.info(request, msg)
        return render(
            request, "ledger/allyledger/alliance_ledger.html", context=context
        )

    alliance_data = AllianceData(
        request=request, alliance=alliance, year=year, month=month, day=day
    )

    # Create the Alliance ledger data
    ledger = alliance_data.generate_ledger_data()

    context = {
        "title": f"Alliance Ledger - {alliance.alliance_name}",
        "alliance_id": alliance_id,
        "billboard": json.dumps(alliance_data.billboard.dict.asdict()),
        "ledger": ledger,
        "years": CorporationWalletJournalEntry.objects.filter(
            division__corporation__corporation__corporation_id__in=alliance_data.corporations
        )
        .values_list("date__year", flat=True)
        .distinct()
        .order_by("-date__year"),
        "totals": alliance_data.calculate_totals(ledger),
        "view": alliance_data.create_view_data(
            viewname="alliance_details",
            alliance_id=alliance_id,
            entity_id=alliance_id,
            section="summary",
        ),
    }
    # Add additional information to the context
    context = add_info_to_context(request, context)

    return render(request, "ledger/allyledger/alliance_ledger.html", context=context)


# pylint: disable=too-many-positional-arguments
@login_required
@permission_required("ledger.advanced_access")
def alliance_details(
    request: WSGIRequest,
    alliance_id=None,
    entity_id=None,
    year=None,
    month=None,
    day=None,
    section=None,
):
    """
    Alliance Details
    """
    perms, alliance = get_alliance(request, alliance_id=alliance_id)

    # pylint: disable=duplicate-code
    if perms is False:
        msg = _("Permission Denied")
        return render(
            request,
            "ledger/partials/information/view_character_content.html",
            {
                "error": msg,
                "alliance_id": alliance_id,
            },
        )
    # pylint: disable=duplicate-code
    if perms is None:
        msg = _("Alliance not found.")
        return render(
            request,
            "ledger/partials/information/view_character_content.html",
            {
                "error": msg,
                "alliance_id": alliance_id,
            },
        )

    alliance_data = AllianceData(
        request=request,
        alliance=alliance,
        year=year,
        month=month,
        day=day,
        section=section,
    )

    # Create the Entity for the ledger
    entity = LedgerEntity(
        entity_id=entity_id,
        alliance_obj=alliance if entity_id == alliance.alliance_id else None,
    )

    journal = alliance_data.filter_entity_journal(entity=entity)
    amounts = alliance_data._create_corporation_details(journal=journal, entity=entity)
    details = alliance_data._add_average_details(request, amounts, day)

    context = {
        "title": f"Alliance Details - {alliance.alliance_name}",
        "type": "alliance",
        "character": details,
        "information": f"Alliance Details - {alliance_data.get_details_title}",
    }
    context = add_info_to_context(request, context)
    # pylint: disable=duplicate-code
    return render(
        request,
        "ledger/partials/information/view_character_content.html",
        context=context,
    )


@login_required
@permission_required("ledger.advanced_access")
def alliance_overview(request):
    """
    Alliance Overview
    """
    context = {
        "title": "Alliance Overview",
    }
    context = add_info_to_context(request, context)
    return render(
        request, "ledger/allyledger/admin/alliance_overview.html", context=context
    )


@login_required
@permission_required("ledger.manage_access")
def alliance_administration(request, alliance_id):
    """
    Alliance Administration
    """
    perm, alliance = get_alliance(request, alliance_id)

    if perm is False:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect("ledger:alliance_ledger_index")
    if perm is None:
        msg = _("Alliance not found.")
        messages.info(request, msg)
        return redirect("ledger:alliance_ledger_index")

    corporations = get_all_corporations_from_alliance(request, alliance.alliance_id)[1]
    all_corporations = EveCorporationInfo.objects.filter(
        alliance__alliance_id=alliance_id
    ).order_by("corporation_name")

    corp_audit_ids = corporations.values_list("corporation__corporation_id", flat=True)
    missing_corporations = all_corporations.exclude(
        corporation_id__in=corp_audit_ids
    ).order_by("corporation_name")

    context = {
        "alliance_id": alliance_id,
        "title": "Alliance Administration",
        "alliance": alliance,
        "corporations": corporations,
        "missing_corporations": missing_corporations,
    }
    context = add_info_to_context(request, context)
    return render(
        request,
        "ledger/allyledger/admin/alliance_administration.html",
        context=context,
    )
