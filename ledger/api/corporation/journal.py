from ninja import NinjaAPI

from ledger.api import schema
from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import CorporationWalletJournalEntry

logger = get_extension_logger(__name__)


class LedgerJournalApiEndpoints:
    tags = ["CorporationJournal"]

    def __init__(self, api: NinjaAPI):

        @api.get(
            "corporation/{corporation_id}/wallet/",
            response={200: list[schema.CorporationWalletEvent], 403: str},
            tags=self.tags,
        )
        def get_corporation_wallet(
            request, corporation_id: int, type_refs: str = "", page: int = 1
        ):
            perms = (
                request.user.has_perm("ledger.admin_access")
                | request.user.has_perm("ledger.corp_audit_admin_manager")
                | request.user.has_perm("ledger.corp_audit_manager")
            )

            if not perms:
                return 403, "Permission Denied"

            wallet_journal = (
                CorporationWalletJournalEntry.get_visible(request.user)
                .filter(
                    division__corporation__corporation__corporation_id=corporation_id
                )
                .select_related("first_party", "second_party", "division")
                .order_by("-entry_id")
            )

            start_count = (page - 1) * 10000
            end_count = page * 10000

            if type_refs:
                refs = type_refs.split(",")
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
