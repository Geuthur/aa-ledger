import logging
from typing import List

from ninja import NinjaAPI
from ninja.pagination import paginate

from django.db.models import Q

from ledger.api import schema
from ledger.api.corporation.helpers import _billboard_corp_ledger
from ledger.api.helpers import Paginator, get_corporations, get_main_and_alts_all
from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import CorporationWalletJournalEntry

logger = get_extension_logger(__name__)


class LedgerApiEndpoints:
    tags = ["CorporationLedger"]

    def __init__(self, api: NinjaAPI):

        @api.get(
            "corporation/{corporation_id}/wallet",
            response={200: List[schema.CorporationWalletEvent], 403: str},
            tags=self.tags,
        )
        @paginate(Paginator)
        def get_corporation_wallet(
            request, corporation_id: int, type_refs: str = "", page: int = 1
        ):
            perms = request.user.has_perm("ledger.basic_access")

            if not perms:
                logging.error("Permission Denied for %s to view wallets!", request.user)
                return 403, "Permission Denied!"

            wallet_journal = (
                CorporationWalletJournalEntry.objects.filter(
                    division__corporation__corporation__corporation_id=corporation_id
                )
                .select_related("first_party", "second_party", "division")
                .order_by("-date")
            )

            start_count = (page - 1) * 10000
            end_count = page * 10000

            if type_refs:
                refs = type_refs.split(",")
                if len(refs) == 0:
                    return 200, []
                wallet_journal = wallet_journal.filter(ref_type__in=refs)

            wallet_journal = wallet_journal[start_count:end_count]

            output = []
            # pylint: disable=duplicate-code
            for w in wallet_journal:
                output.append(
                    {
                        "division": f"{w.division.division} {w.division.name}",
                        "id": w.entry_id,
                        "date": w.date,
                        "first_party": {
                            "id": w.first_party.eve_id,
                            "name": w.first_party.name,
                            "cat": w.first_party.category,
                        },
                        "second_party": {
                            "id": w.second_party.eve_id,
                            "name": w.second_party.name,
                            "cat": w.second_party.category,
                        },
                        "ref_type": w.ref_type,
                        "amount": w.amount,
                        "balance": w.balance,
                        "reason": w.reason,
                    }
                )

            return output

        @api.get(
            "corporation/{corporation_id}/ledger/year/{year}/month/{month}",
            response={200: List[schema.CorporationLedger], 403: str},
            tags=self.tags,
        )
        @paginate(Paginator)
        def get_corporation_ledger(request, corporation_id: int, year: int, month: int):
            perms = request.user.has_perm("ledger.basic_access")

            corporations = [corporation_id]

            if corporation_id == 0:
                character_id = request.user.profile.main_character.character_id
                corporations = get_corporations(request, character_id)

            if not perms:
                logging.error("Permission Denied for %s to view wallets!", request.user)
                return 403, "Permission Denied!"

            # filters &= Q(ref_type=ref_type)
            mains, chars = get_main_and_alts_all(corporations, char_ids=True)

            monthly = True
            filters = Q(
                division__corporation__corporation__corporation_id__in=corporations
            )
            filters &= Q(second_party_id__in=chars)
            filter_date = Q(date__year=year)

            if not month == 0:
                monthly = False
                filter_date &= Q(date__month=month)

            wallet_journal = (
                CorporationWalletJournalEntry.objects.filter(filters, filter_date)
                .prefetch_related(
                    "division",
                    "division__corporation",
                    "division__corporation__corporation",
                    "first_party",
                    "second_party",
                )
                .order_by("-date")
            )

            # Dictionary zur Speicherung der Zusammenfassung für jede main_character_id
            corporation_dict = {}

            # Summary
            summary_total = {}
            summary_total["total_amount"] = 0
            summary_total["total_amount_ess"] = 0
            summary_total["total_amount_all"] = 0

            # Create a Dict for all Mains(including their alts)
            for _, data in mains.items():
                main = data["main"]
                alts = data["alts"]

                chars_mains = [alt.character_id for alt in alts] + [main.character_id]

                alts_names = []

                total_bounty = 0
                total_ess = 0

                char_name = main.character_name
                char_id = main.character_id

                for w in wallet_journal:
                    if w.second_party_id in chars_mains:
                        if w.ref_type == "bounty_prizes":
                            total_bounty += w.amount
                        if w.ref_type == "ess_escrow_transfer":
                            total_ess += w.amount

                combined_amount = total_bounty + total_ess

                if total_bounty or total_ess:
                    corporation_dict[char_id] = {
                        "main_id": char_id,
                        "main_name": char_name,
                        "alt_names": alts_names,
                        "total_amount": total_bounty,
                        "total_amount_ess": total_ess,
                    }

                # Summary all
                summary_total["total_amount"] += total_bounty
                summary_total["total_amount_ess"] += total_ess
                summary_total["total_amount_all"] += combined_amount

            # Billboard
            billboard_dict = _billboard_corp_ledger(
                wallet_journal,
                corporation_dict,
                summary_total["total_amount"],
                monthly,
                year,
                month,
            )

            output = []
            output.append(
                {
                    "ratting": sorted(
                        list(corporation_dict.values()), key=lambda x: x["main_name"]
                    ),
                    "total": summary_total,
                    "billboard": billboard_dict,
                }
            )

            return output
