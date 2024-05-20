"""
Corporation Tax
"""

from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils import timezone

from ledger import app_settings

if app_settings.LEDGER_CORPSTATS_TWO:
    from corpstats.models import CorpMember
else:
    from allianceauth.corputils.models import CorpMember

from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import CorporationWalletJournalEntry, CorpSteuer

logger = get_extension_logger(__name__)
now = timezone.now()


# TODO refactor this class
# pylint: disable=too-many-locals, too-many-branches, too-many-statements
@login_required
@permission_required("ledger.basic_access")
def index_steuer(request):
    """
    Index view
    :param request:
    :return:
    """
    # INIT DATA
    current_date = date.today()
    checked_names_reset = set()
    checked_names = set()
    pre_paid = set()

    wallet_journal = (
        CorporationWalletJournalEntry.objects.prefetch_related(
            "first_party",
            "division",
            "division__corporation",
            "division__corporation__corporation",
        )
        .filter(
            division__corporation__corporation__corporation_id=98128247,
            date__year=current_date.year,
        )
        .order_by("-date")
    )

    # TODO Future Feature
    corps = []

    if request.method == "POST":
        mode = request.POST.get("mode")
        character_id = request.POST.get("character_id")
        character_name = request.POST.get("character_name")
        datepost = request.POST.get("date")

        if mode == "inaktiv":
            CorpSteuer.objects.update_or_create(
                character_id=character_id,
                character_name=character_name,
                defaults={"status": "inactive"},
            )
            messages.success(
                request, f"{character_name} wurde erfolgreich als Inaktiv gesetzt."
            )
            logger.info(
                "%s has set Character: %s to inactive.",
                request.user,
                character_name,
            )

        if mode == "alt":
            CorpSteuer.objects.update_or_create(
                character_id=character_id,
                character_name=character_name,
                defaults={"status": "alt"},
            )
            messages.success(
                request, f"{character_name} wurde erfolgreich als Alt gesetzt."
            )
            logger.info(
                "%s has set Character: %s to alt.",
                request.user,
                character_name,
            )

        if datepost:
            date_obj = datetime.strptime(request.POST.get("date"), "%Y-%m-%d").date()
            CorpSteuer.objects.update_or_create(
                character_id=character_id,
                character_name=character_name,
                defaults={
                    "date": date_obj,
                    "status": "vorauszahlung",
                },
            )
            messages.success(
                request,
                f"{character_name} wurde erfolgreich freigestellt bis {datepost}.",
            )
            logger.info(
                "%s has set Character: %s pre paid till %s.",
                request.user,
                character_name,
                datepost,
            )

        if mode == "reset":
            CorpSteuer.objects.filter(character_id=character_id).delete()
            messages.success(request, f"{character_name} wurde erfolgreich gelöscht.")
            logger.info("%s has reset Character: %s.", request.user, character_name)

    # Alle Mitglieder abrufen
    corp_members = CorpMember.objects.select_related(
        "corpstats", "corpstats__corp"
    ).filter(corpstats__corp__corporation_id__in=corps)

    for corp_member in corp_members:
        # Holen Sie den zugehörigen Eintrag in Corp_Steuer (falls vorhanden)
        corp_steuer_entry = CorpSteuer.objects.filter(
            character_id=corp_member.character_id
        ).first()

        # Überprüfe, ob der Eintrag entweder kein Datum oder ein abgelaufenes Datum hat
        if (
            not corp_steuer_entry
            or corp_steuer_entry.date
            and corp_steuer_entry.date < current_date
        ):
            checked_names.add((corp_member.character_id, corp_member.character_name))
            if (
                corp_member.start_date.month == current_date.month
                and corp_member.start_date.year == current_date.year
            ):
                checked_names.remove(
                    (corp_member.character_id, corp_member.character_name)
                )
        # Überprüfe ob vorausgezahlt wurde
        if (
            corp_steuer_entry
            and corp_steuer_entry.date
            and corp_steuer_entry.date > current_date
        ):
            pre_paid.add((corp_member.character_id, corp_member.character_name))
    # Pending Script -- Init Ende

    output = []
    output_all = []
    output_pending = []
    output_reset = []

    for w in wallet_journal:
        if (
            w.division.division == 5
            and w.amount == 100000000
            and w.date.month == current_date.month
            and w.date.year == current_date.year
        ):
            if (w.first_party.eve_id, w.first_party.name) in checked_names:
                output.append(
                    {
                        "first_party_name": w.first_party.name,
                        "first_party_id": w.first_party.eve_id,
                        "amount": w.amount,
                        "reason": w.reason,
                        "date": w.date.strftime("%Y-%m-%d"),
                    }
                )

            # Pending Month Script
            # Überprüfe, ob das Tupel (character_id, character_name) in checked_names vorhanden ist
            tuple_to_remove = (w.first_party.eve_id, w.first_party.name)

            if tuple_to_remove in checked_names:
                # Entferne das Tupel aus checked_names
                checked_names.remove(tuple_to_remove)

        # All Month
        if w.division.division == 5 and w.amount > 0:
            output_all.append(
                {
                    "first_party_name": w.first_party.name,
                    "first_party_id": w.first_party.eve_id,
                    "amount": w.amount,
                    "reason": w.reason,
                    "date": w.date.strftime("%Y-%m-%d"),
                }
            )
    # Current Month
    for character_id, character_name in pre_paid:
        output.append(
            {
                "first_party_name": character_name,
                "first_party_id": character_id,
                "amount": 100_000_000,
                "reason": "Vorausgezahlt",
                "date": current_date.strftime("%Y-%m"),
            }
        )

    for character_id, character_name in checked_names:
        output_pending.append(
            {
                "character_id": character_id,
                "character_name": character_name,
            }
        )
    # Pending Script POST Ende

    # Reset Script Anfang
    for corp_member in corp_members:
        # Holen Sie den zugehörigen Eintrag in Corp_Steuer (falls vorhanden)
        corp_steuer_entry = CorpSteuer.objects.filter(
            character_id=corp_member.character_id
        ).first()

        if (
            corp_member.start_date.month == current_date.month
            and corp_member.start_date.year == current_date.year
        ):
            checked_names_reset.add(
                (corp_member.character_id, corp_member.character_name, "neuling", "")
            )
        # Überprüfe, ob der Eintrag entweder kein Datum oder ein abgelaufenes Datum hat
        if corp_steuer_entry:
            # Das Datum ist entweder abgelaufen oder nicht vorhanden, füge die character_id und den character_name zur Menge checked_names hinzu
            checked_names_reset.add(
                (
                    corp_member.character_id,
                    corp_member.character_name,
                    corp_steuer_entry.status,
                    corp_steuer_entry.date,
                )
            )

    for character_id, character_name, status, datedata in checked_names_reset:
        output_reset.append(
            {
                "character_id": character_id,
                "character_name": character_name,
                "status": status,
                "date": datedata,
            }
        )
    # Reset Script ENDE

    context = {
        "wallet": output,
        "wallet_all": output_all,
        "wallet_pending": output_pending if wallet_journal else None,
        "wallet_reset": output_reset,
    }

    return render(request, "ledger/corpsteuer/index.html", context)
