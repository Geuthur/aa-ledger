from datetime import datetime
from typing import List

from ninja import NinjaAPI

from django.db.models import Q
from django.shortcuts import render

from ledger.api import schema
from ledger.api.helpers import get_corporations, get_main_and_alts_all
from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import CorporationWalletJournalEntry
from ledger.view_helpers.core import (
    calculate_days_year,
    calculate_ess_stolen,
    calculate_journal,
)

logger = get_extension_logger(__name__)


class LedgerTemplateApiEndpoints:
    tags = ["CorporationLedgerTemplate"]

    def __init__(self, api: NinjaAPI):

        @api.get(
            "corporation/{main_id}/ledger/template/year/{year}/month/{month}",
            response={200: List[schema.CharacterLedgerTemplate], 403: str},
            tags=self.tags,
        )
        def get_corporation_ledger_template(
            request, main_id: int, year: int, month: int
        ):
            overall_mode = False

            perms = request.user.has_perm("ledger.basic_access")

            if main_id == 0:
                overall_mode = True

            if not perms:
                logger.error(
                    "Permission Denied for %s to view corporation ledger template!",
                    request.user,
                )
                return 403, "Permission Denied!"

            current_date = datetime.now()

            total_amount = 0
            total_amount_day = 0
            total_amount_hour = 0
            # ESS
            total_amount_ess = 0
            total_amount_day_ess = 0
            total_amount_hour_ess = 0

            current_date = current_date.replace(year=year)
            if not month == 0:
                current_date = current_date.replace(month=month)

            current_day = calculate_days_year() if month == 0 else current_date.day

            character_id = request.user.profile.main_character.character_id
            corporations = get_corporations(request, character_id)

            mains, chars = get_main_and_alts_all(corporations, char_ids=True)

            filters = Q(second_party_id__in=chars)
            filter_date = Q(date__year=current_date.year)
            if not month == 0:
                filter_date &= Q(date__month=current_date.month)

            wallet_journal = (
                CorporationWalletJournalEntry.objects.filter(filters, filter_date)
                .select_related("first_party", "second_party", "division")
                .values("amount", "date", "second_party_id", "ref_type")
                .order_by("-date")
            )

            if overall_mode:
                mains_data = mains
            else:
                mains_data = {main_id: mains.get(main_id, None)}

            for _, mains_data in mains_data.items():
                main = mains_data["main"]
                alts = mains_data["alts"]

                # Each Chars from a Main Character
                chars = [alt.character_id for alt in alts] + [main.character_id]

                char_name = main.character_name if not main_id == 0 else "Summary"
                char_id = main.character_id if not main_id == 0 else 0

                my_filter = Q(second_party_id__in=chars)
                my_filter_bounty = my_filter & Q(ref_type="bounty_prizes")
                my_filter_ess_payout = my_filter & Q(ref_type="ess_escrow_transfer")

                amount_ess = calculate_journal(wallet_journal, my_filter_ess_payout)

                amount_bounty = calculate_journal(
                    wallet_journal,
                    my_filter_bounty,
                )

                # Berechne die Gesamtsumme für alle Charaktere
                total_amount += amount_bounty["total_amount"]
                total_amount_day += amount_bounty["total_amount_day"]
                total_amount_hour += amount_bounty["total_amount_hour"]

                # ESS
                total_amount_ess += amount_ess["total_amount"]
                total_amount_day_ess += amount_ess["total_amount_day"]
                total_amount_hour_ess += amount_ess["total_amount_hour"]

            stolen = 0
            gain = 0

            # If not 0 then add to Rattingledger
            if total_amount > 0:
                stolen, gain = calculate_ess_stolen(total_amount, total_amount_ess)

            day_avg_isk = round(total_amount / current_day)
            day_avg_ess = round(total_amount_ess / current_day)

            hourly_avg_isk = round((total_amount / current_day) / 24)
            hourly_avg_ess = round((total_amount_ess / current_day) / 24)

            total_summary = total_amount + total_amount_ess
            total_summary_day = total_amount_day + total_amount_day_ess
            total_summary_hour = total_amount_hour + total_amount_hour_ess

            # pylint: disable=duplicate-code
            summary = {
                "main_name": char_name,
                "main_id": char_id,
                "date": (
                    str(current_date.year)
                    if month == 0
                    else current_date.strftime("%B")
                ),
                "summary_isk": total_amount,
                "summary_ess": total_amount_ess,
                "summary": total_summary,
                "day_avg_isk": day_avg_isk,
                "day_avg_ess": day_avg_ess,
                "summary_day": total_summary_day,
                "hourly_avg_isk": hourly_avg_isk,
                "hourly_avg_ess": hourly_avg_ess,
                "summary_hour": total_summary_hour,
            }
            if not overall_mode:
                summary.update(
                    {
                        "day_isk": total_amount_day,
                        "day_ess": total_amount_day_ess,
                        "hourly_isk": total_amount_hour,
                        "hourly_ess": total_amount_hour_ess,
                    }
                )
            if stolen:
                day_stolen = round(stolen / current_date.day)
                hourly_stolen = round((stolen / current_date.day) / 24)

                summary.update(
                    {
                        "gain": gain,
                        "stolen": stolen,
                        "day_stolen": day_stolen,
                        "hourly_stolen": hourly_stolen,
                    }
                )

            context = {"character": summary}

            return render(
                request, "ledger/modals/pve/view_character_content.html", context
            )
