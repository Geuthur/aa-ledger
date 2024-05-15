from decimal import Decimal
from typing import List

from ninja import NinjaAPI
from ninja.pagination import paginate

from django.db.models import DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce

from ledger import app_settings
from ledger.api import schema
from ledger.api.character.helpers import _billboard_char_ledger
from ledger.api.helpers import Paginator, get_alts_queryset, get_main_character
from ledger.models.corporationaudit import CorporationWalletJournalEntry
from ledger.view_helpers.core import events_filter

if app_settings.MEMBERAUDIT_USE:
    from memberaudit.models import CharacterMiningLedgerEntry as CharacterMiningLedger
    from memberaudit.models import CharacterWalletJournalEntry
else:
    from ledger.models.characteraudit import (
        CharacterWalletJournalEntry,
        CharacterMiningLedger,
    )

from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)

SR_CHAR = (
    "character__eve_character"
    if app_settings.MEMBERAUDIT_USE
    else "character__character"
)


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
            "account/{character_id}/ledger/year/{year}/month/{month}",
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

            monthly = True
            filters = (
                Q(character__eve_character__in=characters)
                if app_settings.MEMBERAUDIT_USE
                else Q(character__character__in=characters)
            )
            filter_date = Q(date__year=year)
            if not month == 0:
                filter_date &= Q(date__month=month)
                monthly = False

            chars = [char.character_id for char in characters]

            entries_filter = Q(second_party_id__in=chars) | Q(first_party_id__in=chars)

            # Dictionary zur Speicherung der Zusammenfassung für jede main_character_id
            summary_dict = {}
            summary_dict_total = {}
            billboard_dict = {}

            summary_dict_total["total_amount"] = 0
            summary_dict_total["total_amount_ess"] = 0
            summary_dict_total["total_amount_others"] = 0
            summary_dict_total["total_amount_all"] = 0
            summary_dict_total["total_amount_mining"] = 0

            wallet_journal = (
                CharacterWalletJournalEntry.objects.filter(filters, filter_date)
                .select_related("first_party", "second_party", SR_CHAR)
                .order_by("-date")
            )

            corporation_journal = (
                CorporationWalletJournalEntry.objects.filter(
                    entries_filter, filter_date
                )
                .select_related("first_party", "second_party")
                .order_by("-date")
            )

            # Exclude Events to avoid wrong stats
            corporation_journal = events_filter(corporation_journal)
            mining_entries_data = (
                CharacterMiningLedger.objects.filter(filters, filter_date)
                .select_related(SR_CHAR)
                .order_by("-date")
            )

            mining_entries_data = mining_entries_data.annotate_pricing()

            # TODO Field Tax and Amount
            # Ratting, Others
            for char in characters:
                char_id = char.character_id
                char_name = char.character_name

                # Core
                filter_ledger = Q(second_party_id=char_id)

                # Industry
                filter_market = filter_ledger & Q(ref_type="market_transaction")
                filter_contracts = filter_ledger & Q(
                    ref_type__in=[
                        "contract_price_payment_corp",
                        "contract_reward",
                        "contract_price",
                    ],
                    amount__gt=0,
                )
                filter_donations = filter_ledger & Q(ref_type="player_donation")

                # Ratting
                filter_bounty = filter_ledger & Q(ref_type="bounty_prizes")
                filter_ess = filter_ledger & Q(ref_type="ess_escrow_transfer")
                # Mining
                filter_mining = (
                    Q(character__eve_character__character_id=char_id)
                    if app_settings.MEMBERAUDIT_USE
                    else Q(character__character__character_id=char_id)
                )

                amount_bounty = wallet_journal.filter(filter_bounty).aggregate(
                    total_amount=Coalesce(
                        Sum(F("amount")), 0, output_field=DecimalField()
                    )
                )

                amount_ess = corporation_journal.filter(filter_ess).aggregate(
                    total_amount=Coalesce(
                        Sum(F("amount")), 0, output_field=DecimalField()
                    )
                )

                amount_contracts = wallet_journal.filter(filter_contracts).aggregate(
                    total_amount=Coalesce(
                        Sum(F("amount")), 0, output_field=DecimalField()
                    )
                )

                amount_transactions = wallet_journal.filter(filter_market).aggregate(
                    total_amount=Coalesce(
                        Sum(F("amount")), 0, output_field=DecimalField()
                    )
                )

                amount_donations = (
                    wallet_journal.filter(filter_donations)
                    .exclude(first_party_id__in=chars)
                    .aggregate(
                        total_amount=Coalesce(
                            Sum(F("amount")), 0, output_field=DecimalField()
                        )
                    )
                )

                amount_mining = (
                    mining_entries_data.filter(filter_date, filter_mining)
                    .values("total", "date")
                    .aggregate(
                        total_amount=Coalesce(
                            Sum(F("total")), 0, output_field=DecimalField()
                        )
                    )
                )

                amount_ess["total_amount"] = Decimal(
                    (amount_ess["total_amount"] / app_settings.CORP_TAX)
                    * (100 - app_settings.CORP_TAX)
                )
                total_amount_others = (
                    amount_contracts["total_amount"]
                    + amount_transactions["total_amount"]
                    + amount_donations["total_amount"]
                )
                combined_amount = (
                    amount_bounty["total_amount"]
                    + amount_ess["total_amount"]
                    + total_amount_others
                )

                if amount_bounty["total_amount"] > 0 or total_amount_others > 0:
                    summary_dict[char_id] = {
                        "main_id": char_id,
                        "main_name": char_name,
                        "total_amount": amount_bounty["total_amount"],
                        "total_amount_ess": amount_ess["total_amount"],
                        "total_amount_mining": amount_mining["total_amount"],
                        "total_amount_others": total_amount_others,
                    }

                # Total Amount
                summary_dict_total["total_amount"] += amount_bounty["total_amount"]
                # ESS
                summary_dict_total["total_amount_ess"] += amount_ess["total_amount"]
                # Mined
                summary_dict_total["total_amount_mining"] += amount_mining[
                    "total_amount"
                ]
                # others
                summary_dict_total["total_amount_others"] += total_amount_others
                # Combined
                summary_dict_total["total_amount_all"] += combined_amount

            # Save Dicts & Models for billboard function
            models = wallet_journal, corporation_journal
            # dicts = summary_dict, summary_dict_total
            # Outsource Function to Create Billboard Data
            billboard_dict = _billboard_char_ledger(
                models, mining_entries_data, monthly, year, month
            )

            summary_dict_total["total_amount_all"] += Decimal(
                summary_dict_total["total_amount_mining"]
            )

            output = []

            output.append(
                {
                    "ratting": sorted(
                        list(summary_dict.values()), key=lambda x: x["main_name"]
                    ),
                    "total": summary_dict_total,
                    "billboard": billboard_dict,
                }
            )

            return output
