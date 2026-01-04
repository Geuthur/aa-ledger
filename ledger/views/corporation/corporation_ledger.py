"""PvE Views"""

# Standard Library
from http import HTTPStatus

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__, forms, tasks
from ledger.api.helpers.core import (
    get_corporationowner_or_none,
    get_manage_corporation,
)
from ledger.helpers import data_exporter
from ledger.models.corporationaudit import (
    CorporationOwner,
)
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


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
    perms = get_corporationowner_or_none(request, corporation_id)[0]

    kwargs = {
        "corporation_id": corporation_id,
    }

    if request.POST:
        division_id = request.POST.get("division") or None
        year = request.POST.get("year") or None
        month = request.POST.get("month") or None
        day = request.POST.get("day") or None
        # Ensure that if only day is provided, month is also provided
        if day is not None and month is None:
            month = timezone.now().month

    if division_id is not None:
        kwargs["division_id"] = division_id
    if year is not None:
        kwargs["year"] = year
    if month is not None:
        kwargs["month"] = month
    if day is not None:
        kwargs["day"] = day

    # Redirect to the same view with updated parameters
    if request.POST:
        return redirect("ledger:corporation_ledger", **kwargs)

    ledger_url = reverse("ledger:api:get_corporation_ledger", kwargs=kwargs)

    context = {
        "title": "Corporation Ledger",
        "corporation_id": corporation_id,
        "ledger_url": ledger_url,
        "forms": {
            "corporation_dropdown": forms.CorporationDropdownForm(
                corporation_id=corporation_id,
                division_id=division_id,
                year=year,
                month=month,
                day=day,
            ),
        },
    }

    if not perms:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return render(request, "ledger/view-corporation-ledger.html", context=context)
    return render(request, "ledger/view-corporation-ledger.html", context=context)


@login_required
@permission_required("ledger.advanced_access")
def corporation_overview(request):
    """
    Corporation Overview
    """
    context = {
        "title": "Corporation Overview",
        "year": timezone.now().year,
        "month": timezone.now().month,
    }
    return render(request, "ledger/view-corporation-overview.html", context=context)


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
        return redirect("ledger:corporation_overview")

    if perm is None:
        msg = _("Corporation not found")
        messages.info(request, msg)
        return redirect("ledger:corporation_overview")

    # TODO Get Missing Characters from esi-corporations.read_corporation_membership.v1 ?
    corp_characters = CharacterOwnership.objects.filter(
        character__corporation_id=corporation.eve_corporation.corporation_id
    ).order_by("character__character_name")
    corporation_dataexporter = data_exporter.LedgerCSVExporter.create_exporter(
        "corporation", corporation_id
    )

    context = {
        "corporation_id": corporation_id,
        "title": "Corporation Administration",
        "year": timezone.now().year,
        "month": timezone.now().month,
        "corporation": corporation,
        "characters": corp_characters,
        "is_exportable": corporation_dataexporter.has_data,
    }
    return render(
        request,
        "ledger/view-corporation-administration.html",
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

    audit = CorporationOwner.objects.get(eve_corporation__corporation_id=corporation_id)
    audit.delete()

    msg = _(f"{audit.eve_corporation.corporation_name} successfully deleted")
    return JsonResponse(
        {"success": True, "message": msg}, status=HTTPStatus.OK, safe=False
    )


@login_required
@permission_required("ledger.basic_access")
def corporation_data_export(request, corporation_id: int):
    """Data Export View"""
    perms = get_manage_corporation(request, corporation_id)[0]

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
    perms = get_manage_corporation(request, corporation_id)[0]
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
    perms = get_manage_corporation(request, entity_id)[0]
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
