import logging
from typing import List

from ninja import NinjaAPI

from ledger.api import schema
from ledger.api.helpers import get_corporations, get_main_and_alts_all
from ledger.api.managers.ledger_manager import JournalProcess
from ledger.app_settings import IS_TESTING
from ledger.hooks import get_extension_logger
from ledger.view_helpers.core import _storage_key, get_cache_stale, set_cache_hourly

logger = get_extension_logger(__name__)


class LedgerApiEndpoints:
    tags = ["CorporationLedger"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/ledger/year/{year}/month/{month}/",
            response={200: List[schema.CorporationLedger], 403: str},
            tags=self.tags,
        )
        def get_corporation_ledger(request, corporation_id: int, year: int, month: int):
            perms = request.user.has_perm("ledger.basic_access")

            corporations = [corporation_id]

            if corporation_id == 0:
                corporations = get_corporations(request)

            if not perms:
                logging.error("Permission Denied for %s to view wallets!", request.user)
                return 403, "Permission Denied!"

            output = get_cache_stale(
                _storage_key(f"corporation_ledger_{corporation_id}_{year}_{month}")
            )

            # Create the Ledger
            if not output:
                characters, chars_list = get_main_and_alts_all(
                    corporations, char_ids=True
                )

                ledger = JournalProcess(characters, year, month)
                output = ledger.corporation_ledger(chars_list)
                if not IS_TESTING:
                    set_cache_hourly(
                        output,
                        _storage_key(
                            f"corporation_ledger_{corporation_id}_{year}_{month}"
                        ),
                    )

            return output
