"""PvE Views"""

# Standard Library
import json
from http import HTTPStatus

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__, forms, tasks
from ledger.api.helpers import (
    get_corporation,
    get_manage_corporation,
)
from ledger.helpers import data_exporter
from ledger.helpers.core import add_info_to_context
from ledger.helpers.corporation import CorporationData, LedgerEntity
from ledger.models.corporationaudit import (
    CorporationAudit,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@permission_required("ledger.advanced_access")
def corporation_ledger_index(request):
    """Corporation Ledger Index View"""
    context = {}
    context = add_info_to_context(request, context)
    return redirect(
        "ledger:corporation_ledger", request.user.profile.main_character.corporation_id
    )


@login_required
@permission_required("ledger.basic_access")
def corporation_data_export(request, corporation_id: int):
    """Data Export View"""
    perms = get_corporation(request, corporation_id)[0]

    corporation_exporter = data_exporter.LedgerCSVExporter.create_exporter(
        "corporation", corporation_id
    )
    files = corporation_exporter.gather_export_files()

    context = {
        "title": "Data Export",
        "corporation_id": corporation_id,
        "files": files,
        "is_exportable": corporation_exporter.has_data,
    }

    if perms is False:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return render(request, "ledger/data-export.html", context=context)

    if perms is None:
        msg = _("Corporation not found")
        messages.info(request, msg)
        return render(request, "ledger/data-export.html", context=context)

    context.update(
        {
            "forms": {
                "generate_data_export": forms.GenerateDataExportForm(
                    corporation_id=corporation_id
                ),
            },
        }
    )

    context = add_info_to_context(request, context)
    return render(request, "ledger/data-export.html", context)


@login_required
@permission_required("ledger.manage_access")
# pylint: disable=unused-argument
def corporation_download_export_file(
    request,
    hash_code: str,
) -> FileResponse:
    """Render file view for downloading an export file."""
    entity_id, division_id, year, month = data_exporter.LedgerCSVExporter.decoder(
        hash_code
    )
    exporter = data_exporter.LedgerCSVExporter.create_exporter(
        "corporation", entity_id, division_id=division_id, year=year, month=month
    )
    destination = data_exporter.default_destination()
    zip_file = destination / exporter.output_basename.with_suffix(".zip")
    if not zip_file.exists():
        raise Http404(f"Could not find export file for corporation {entity_id}")
    logger.info("Returning file %s for download of topic %s", zip_file, "corporation")
    return FileResponse(zip_file.open("rb"))


@login_required
@permission_required("ledger.manage_access")
@require_POST
def corporation_data_export_generate(request, corporation_id: int):
    """Handle POST form to generate a data export for a corporation."""
    perms = get_corporation(request, corporation_id)[0]
    if perms is False:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect("ledger:corporation_data_export", corporation_id=corporation_id)

    if perms is None:
        msg = _("Corporation not found")
        messages.info(request, msg)
        return redirect("ledger:corporation_data_export", corporation_id=corporation_id)

    form = forms.GenerateDataExportForm(
        request.POST,
        corporation_id=corporation_id,
    )

    if not form.is_valid():
        msg = _("Invalid form submission.")
        messages.error(request, msg)
        return redirect("ledger:corporation_data_export", corporation_id=corporation_id)

    # Read optional form values
    year_val = form.cleaned_data.get("year")
    month_val = form.cleaned_data.get("month") or None

    division_obj = form.cleaned_data.get("division")
    division_val = division_obj.division_id if division_obj is not None else None

    logger.debug("Generating data export for year=%s, month=%s", year_val, month_val)
    tasks.export_data_ledger.apply_async(
        kwargs={
            "user_pk": request.user.pk,
            "ledger_type": "corporation",
            "entity_id": corporation_id,
            "division_id": division_val,
            "year": year_val,
            "month": month_val,
        },
        priority=7,
    )
    msg = _(
        f"Data export for {corporation_id} has been started. This can take a couple of minutes. You will get a notification once it is completed."
    )
    messages.info(request, msg)
    return redirect("ledger:corporation_data_export", corporation_id=corporation_id)


@login_required
@permission_required("ledger.manage_access")
def corporation_data_export_run_update(
    request,
    hash_code: str,
):
    """Render view for running data export update."""
    entity_id, division_id, year, month = data_exporter.LedgerCSVExporter.decoder(
        hash_code
    )

    logger.debug(
        "Running data export update for entity_id=%s, division_id=%s, year=%s, month=%s",
        entity_id,
        division_id,
        year,
        month,
    )
    perms = get_corporation(request, entity_id)[0]
    if perms is False:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect("ledger:corporation_data_export", corporation_id=entity_id)

    if perms is None:
        msg = _("Corporation not found")
        messages.info(request, msg)
        return redirect("ledger:corporation_data_export", corporation_id=entity_id)

    tasks.export_data_ledger.apply_async(
        kwargs={
            "user_pk": request.user.pk,
            "ledger_type": "corporation",
            "entity_id": entity_id,
            "division_id": division_id,
            "year": year,
            "month": month,
        },
        priority=7,
    )
    msg = _(
        f"Data export for {entity_id} has been started. This can take a couple of minutes. You will get a notification once it is completed."
    )
    messages.info(request, msg)
    return redirect("ledger:corporation_data_export", corporation_id=entity_id)


# pylint: disable=too-many-positional-arguments
@login_required
@permission_required("ledger.advanced_access")
def corporation_ledger(
    request: WSGIRequest,
    corporation_id: int,
    division_id: int = None,
    year: int = None,
    month: int = None,
    day: int = None,
):
    """
    Corporation Ledger
    """
    perms, corporation = get_corporation(request, corporation_id)

    context = {
        "title": "Corporation Ledger",
        "corporation_id": corporation_id,
        "disabled": True,
    }

    # pylint: disable=duplicate-code
    if perms is False:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return render(
            request, "ledger/corpledger/corporation_ledger.html", context=context
        )
    # pylint: disable=duplicate-code
    if perms is None:
        msg = _("Corporation not found")
        messages.info(request, msg)
        return render(
            request, "ledger/corpledger/corporation_ledger.html", context=context
        )

    corporation_data = CorporationData(
        corporation=corporation,
        division_id=division_id,
        year=year,
        month=month,
        day=day,
    )
    # Create the Corporation ledger data
    ledger = corporation_data.generate_ledger_data()

    context = {
        "title": f"Corporation Ledger - {corporation.corporation.corporation_name}",
        "corporation_id": corporation_id,
        "division_id": division_id,
        "billboard": json.dumps(corporation_data.billboard.dict.asdict()),
        "ledger": ledger,
        "divisions": corporation_data.divisions,
        "years": corporation_data.activity_years,
        "totals": corporation_data.calculate_totals(ledger),
        "view": corporation_data.create_view_data(
            viewname="corporation_details",
            corporation_id=corporation_id,
            entity_id=corporation_id,
            division_id=division_id,
            section="summary",
        ),
    }
    # Add additional information to the context
    context = add_info_to_context(request, context)

    return render(request, "ledger/corpledger/corporation_ledger.html", context=context)


# pylint: disable=too-many-positional-arguments, too-many-arguments
@login_required
@permission_required("ledger.advanced_access")
def corporation_details(
    request: WSGIRequest,
    corporation_id: int,
    entity_id: int,
    division_id: int = None,
    year: int = None,
    month: int = None,
    day: int = None,
    section: str = None,
):
    """
    Corporation Details
    """
    perms, corporation = get_corporation(request, corporation_id)

    context = {
        "title": "Corporation Ledger",
        "corporation_id": corporation_id,
    }

    # pylint: disable=duplicate-code
    if perms is False:
        msg = _("Permission Denied")
        return render(
            request,
            "ledger/partials/information/view_character_content.html",
            {
                "error": msg,
                "corporation_id": corporation_id,
            },
        )
    # pylint: disable=duplicate-code
    if perms is None:
        msg = _("Corporation not found")
        return render(
            request,
            "ledger/partials/information/view_character_content.html",
            {
                "error": msg,
                "corporation_id": corporation_id,
            },
        )

    corporation_data = CorporationData(
        corporation=corporation,
        division_id=division_id,
        year=year,
        month=month,
        day=day,
        section=section,
    )

    # Create the Entity for the ledger
    entity = LedgerEntity(
        entity_id=entity_id,
    )

    journal = corporation_data.filter_entity_journal(entity=entity)
    amounts = corporation_data._create_corporation_details(
        journal=journal, entity=entity
    )
    details = corporation_data._add_average_details(request, amounts, day)

    context = {
        "title": f"Corporation Details - {corporation.corporation_name}",
        "type": "corporation",
        "character": details,
        "information": f"Corporation Details - {corporation_data.get_details_title}",
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
def corporation_overview(request):
    """
    Corporation Overview
    """
    context = {"title": "Corporation Overview"}
    context = add_info_to_context(request, context)
    return render(
        request, "ledger/corpledger/admin/corporation_overview.html", context=context
    )


@login_required
@permission_required("ledger.manage_access")
def corporation_administration(request, corporation_id):
    """
    Corporation Administration
    """
    perm, corporation = get_manage_corporation(request, corporation_id)

    if perm is False:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect("ledger:corporation_ledger_index")

    if perm is None:
        msg = _("Corporation not found")
        messages.info(request, msg)
        return redirect("ledger:corporation_ledger_index")

    # TODO Get Missing Characters from esi-corporations.read_corporation_membership.v1 ?
    corp_characters = CharacterOwnership.objects.filter(
        character__corporation_id=corporation.corporation.corporation_id
    ).order_by("character__character_name")
    corporation_dataexporter = data_exporter.LedgerCSVExporter.create_exporter(
        "corporation", corporation_id
    )

    context = {
        "corporation_id": corporation_id,
        "title": "Corporation Administration",
        "corporation": corporation,
        "characters": corp_characters,
        "is_exportable": corporation_dataexporter.has_data,
    }
    context = add_info_to_context(request, context)

    return render(
        request,
        "ledger/corpledger/admin/corporation_administration.html",
        context=context,
    )


@login_required
@permission_required("ledger.manage_access")
@require_POST
def corporation_delete(request, corporation_id):
    """
    Character Delete
    """
    perms = get_manage_corporation(request, corporation_id)[0]

    if perms is False:
        msg = _("Permission Denied")
        return JsonResponse(
            {"success": False, "message": msg}, status=HTTPStatus.FORBIDDEN, safe=False
        )
    if perms is None:
        msg = _("Corporation not found")
        return JsonResponse(
            {"success": False, "message": msg}, status=HTTPStatus.NOT_FOUND, safe=False
        )

    audit = CorporationAudit.objects.get(corporation__corporation_id=corporation_id)
    audit.delete()

    msg = _(f"{audit.corporation.corporation_name} successfully deleted")
    return JsonResponse(
        {"success": True, "message": msg}, status=HTTPStatus.OK, safe=False
    )
