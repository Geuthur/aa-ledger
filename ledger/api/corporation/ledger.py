import logging
from typing import List

from ninja import NinjaAPI
from ninja.pagination import paginate

from ledger.api import schema
from ledger.api.helpers import Paginator, get_corporations, get_main_and_alts_all
from ledger.api.ledgermanager import JournalProcess
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
            "corporation/{corporation_id}/ledger/year/{year}/month/{month}/",
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
            characters, chars_list = get_main_and_alts_all(corporations, char_ids=True)

            # Create the Ledger
            ledger = JournalProcess(characters, year, month)
            output = ledger.corporation_ledger(corporations, chars_list)

            return output
