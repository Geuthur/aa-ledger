from typing import List

from ninja import NinjaAPI
from ninja.pagination import paginate

from django.db.models import Q

from ledger import app_settings
from ledger.api import schema
from ledger.api.helpers import Paginator, get_alts_queryset, get_main_character
from ledger.api.ledgermanager import JournalProcess

if app_settings.LEDGER_MEMBERAUDIT_USE:
    from memberaudit.models import CharacterWalletJournalEntry
else:
    from ledger.models.characteraudit import (
        CharacterWalletJournalEntry,
    )

from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)

SR_CHAR = (
    "character__eve_character"
    if app_settings.LEDGER_MEMBERAUDIT_USE
    else "character__character"
)


def get_filters(characters, year, month):
    filters = (
        Q(character__eve_character__in=characters)
        if app_settings.LEDGER_MEMBERAUDIT_USE
        else Q(character__character__in=characters)
    )
    filter_date = Q(date__year=year)
    if not month == 0:
        filter_date &= Q(date__month=month)

    chars = [char.character_id for char in characters]

    entries_filter = Q(second_party_id__in=chars) | Q(first_party_id__in=chars)

    return filters, filter_date, entries_filter


class LedgerApiEndpoints:
    tags = ["CharacerLedger"]

    def __init__(self, api: NinjaAPI):

        @api.get(
            "account/{character_id}/wallet",
            response={200: List[schema.CharacterWalletEvent], 403: str},
            tags=self.tags,
        )
        @paginate(Paginator)
        def get_character_wallet(request, character_id: int):
            if character_id == 0:
                character_id = request.user.profile.main_character.character_id
            response, main = get_main_character(request, character_id)

            if not response:
                return 403, "Permission Denied"

            characters = get_alts_queryset(main)

            wallet_journal = (
                CharacterWalletJournalEntry.objects.filter(
                    character__character__in=characters
                )
                .select_related("first_party", "second_party", SR_CHAR)
                .order_by("-date")[:35000]
            )
            output = []

            for w in wallet_journal:
                output.append(
                    {
                        "character": w.character.eve_character,
                        "id": w.entry_id,
                        "date": w.date,
                        "first_party": {
                            "id": w.first_party_id,
                            "name": w.first_party.name,
                            "cat": w.first_party.category,
                        },
                        "second_party": {
                            "id": w.second_party_id,
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
            "account/{character_id}/ledger/year/{year}/month/{month}/",
            response={200: List[schema.CharacterLedger], 403: str},
            tags=self.tags,
        )
        @paginate(Paginator)
        def get_character_ledger(request, character_id: int, year: int, month: int):
            if character_id == 0:
                character_id = request.user.profile.main_character.character_id
            response, main = get_main_character(request, character_id)

            if not response:
                return 403, "Permission Denied"

            characters = get_alts_queryset(main)

            # Create the Ledger
            ledger = JournalProcess(characters, year, month)
            output = ledger.character_ledger()

            return output
