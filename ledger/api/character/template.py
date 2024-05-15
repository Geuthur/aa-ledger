from datetime import datetime
from decimal import Decimal
from typing import List

from ninja import NinjaAPI

from django.db.models import F, Q, Sum
from django.shortcuts import render

from allianceauth.eveonline.models import EveCharacter

from ledger import app_settings

if app_settings.MEMBERAUDIT_USE:
    from memberaudit.models import CharacterMiningLedgerEntry as CharacterMiningLedger
    from memberaudit.models import CharacterWalletJournalEntry
else:
    from ledger.models.characteraudit import (
        CharacterWalletJournalEntry,
        CharacterMiningLedger,
    )

from ledger.api import schema
from ledger.api.helpers import get_alts_queryset, get_main_character
from ledger.app_settings import CORP_TAX
from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import CorporationWalletJournalEntry
from ledger.view_helpers.core import (
    calculate_days_year,
    calculate_ess_stolen,
    calculate_journal,
    events_filter,
)

logger = get_extension_logger(__name__)


class LedgerTemplateApiEndpoints:
    tags = ["CharacerLedgerTemplate"]

    def __init__(self, api: NinjaAPI):

        @api.get(
            "account/{character_id}/ledger/template/year/{year}/month/{month}",
            response={200: List[schema.CharacterLedgerTemplate], 403: str},
            tags=self.tags,
        )
        def get_character_ledger_template(
            request,
            character_id: int,
            year: int,
            month: int,
            **kwargs,  # pylint: disable=unused-argument
        ):
            overall_mode = False

            if character_id == 0:
                character_id = request.user.profile.main_character.character_id
                overall_mode = True
            response, main = get_main_character(request, character_id)

            current_date = datetime.now()

            current_date = current_date.replace(year=year)
            if not month == 0:
                current_date = current_date.replace(month=month)

            if not response:
                return 403, "Permission Denied"

            alts = get_alts_queryset(main)

            main = EveCharacter.objects.get(character_id=character_id)

            current_day = calculate_days_year() if month == 0 else current_date.day

            characters = alts if overall_mode else [main]

            filters = Q(character__eve_character__in=characters)
            filter_date = Q(date__year=current_date.year)
            if not month == 0:
                filter_date &= Q(date__month=current_date.month)

            chars = (
                [char.character_id for char in characters]
                if overall_mode
                else [main.character_id]
            )

            chars_list = [char.character_id for char in alts]

            entries_filter = Q(second_party_id__in=chars) | Q(first_party_id__in=chars)

            # pylint: disable=duplicate-code
            wallet_template_journal = (
                CharacterWalletJournalEntry.objects.filter(filters, filter_date)
                .select_related(
                    "first_party", "second_party", "character__eve_character"
                )
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
                .select_related("character__eve_character")
                .order_by("-date")
            )

            mining_entries_data = mining_entries_data.annotate_pricing()

            total_amount = {}
            total_amount_day = {}
            total_amount_hour = {}

            amount = {}

            total_list = [
                "total",
                "ess",
                "transaction",
                "contract",
                "donation",
                "production_cost",
                "market_cost",
                "mining",
            ]

            for total in total_list:
                total_amount[total] = 0
                total_amount_day[total] = 0
                total_amount_hour[total] = 0
            stolen = None

            for char in characters:
                char_id = char.character_id
                char_name = char.character_name

                my_filter = Q(second_party_id=char_id) | Q(first_party_id=char_id)

                my_filter_market = my_filter & Q(ref_type="market_transaction")
                my_filter_market_cost = my_filter & Q(
                    ref_type__in=[
                        "transaction_tax",
                        "market_provider_tax",
                        "brokers_fee",
                    ]
                )
                my_filter_production = my_filter & Q(
                    ref_type__in=["industry_job_tax", "manufacturing"]
                )
                my_filter_contracts = my_filter & Q(
                    ref_type__in=[
                        "contract_price_payment_corp",
                        "contract_reward",
                        "contract_price",
                    ],
                    amount__gt=0,
                )
                my_filter_donations = my_filter & Q(ref_type="player_donation")

                my_filter_bounty = my_filter & Q(ref_type="bounty_prizes")
                my_filter_ess = my_filter & Q(ref_type="ess_escrow_transfer")
                filter_mining = Q(character__eve_character__character_id=char_id)

                amount["total"] = calculate_journal(
                    wallet_template_journal,
                    my_filter_bounty,
                )

                amount["ess"] = calculate_journal(
                    corporation_journal,
                    my_filter_ess,
                )

                amount["transaction"] = calculate_journal(
                    wallet_template_journal,
                    my_filter_market,
                )

                amount["production_cost"] = calculate_journal(
                    wallet_template_journal,
                    my_filter_production,
                )

                amount["market_cost"] = calculate_journal(
                    wallet_template_journal,
                    my_filter_market_cost,
                )

                amount["contract"] = calculate_journal(
                    wallet_template_journal,
                    my_filter_contracts,
                )

                amount["donation"] = calculate_journal(
                    wallet_template_journal,
                    my_filter_donations,
                    exclude=chars_list,
                )

                # Mining Ledger
                amount["mining"] = {}
                amount["mining"]["total_amount"] = 0
                amount["mining"]["total_amount_day"] = 0
                amount["mining"]["total_amount_hour"] = 0

                mining_aggregated = (
                    mining_entries_data.filter(filter_date, filter_mining)
                    .values("total", "date")
                    .aggregate(
                        total_amount=Sum(F("total")),
                        total_amount_day=Sum(
                            F("total"), filter=Q(date__day=current_date.day)
                        ),
                    )
                )

                amount["mining"]["total_amount"] += Decimal(
                    mining_aggregated["total_amount"] or 0
                )
                amount["mining"]["total_amount_day"] += Decimal(
                    mining_aggregated["total_amount_day"] or 0
                )
                amount["mining"]["total_amount_hour"] += Decimal(
                    amount["mining"]["total_amount_day"] / 24
                )

                # Calculate ESS Payout Char
                amount["ess"]["total_amount"] = Decimal(
                    (amount["ess"]["total_amount"] / CORP_TAX) * (100 - CORP_TAX)
                )
                amount["ess"]["total_amount_day"] = Decimal(
                    (amount["ess"]["total_amount_day"] / CORP_TAX) * (100 - CORP_TAX)
                )
                amount["ess"]["total_amount_hour"] = Decimal(
                    (amount["ess"]["total_amount_hour"] / CORP_TAX) * (100 - CORP_TAX)
                )

                # Sum Total Amounts
                for total in total_list:
                    if amount[total]["total_amount"]:
                        total_amount[total] += amount[total]["total_amount"]
                        total_amount_day[total] += amount[total]["total_amount_day"]
                        total_amount_hour[total] += amount[total]["total_amount_hour"]
            gain = 0
            stolen_day = 0
            # If not 0 then add to Rattingledger
            if total_amount["total"] > 0:
                stolen, gain = calculate_ess_stolen(
                    total_amount["total"], total_amount["ess"]
                )
                stolen_day, _ = calculate_ess_stolen(
                    total_amount_day["total"], total_amount_day["ess"]
                )

            day_avg_isk = round(total_amount["total"] / current_day)
            day_avg_ess = round(total_amount["ess"] / current_day)

            hourly_avg_isk = round((total_amount["total"] / current_day) / 24)
            hourly_avg_ess = round((total_amount["ess"] / current_day) / 24)

            total_summary = sum(
                total_amount[key] for key in total_list if key in total_amount
            )
            total_summary_day = sum(
                total_amount_day[key] for key in total_list if key in total_amount_day
            )
            total_summary_hour = sum(
                total_amount_hour[key] for key in total_list if key in total_amount_hour
            )

            main_name = char_name if not overall_mode else "Summary"
            main_id = char_id if not overall_mode else 0

            summary = {
                "main_name": main_name,
                "main_id": main_id,
                "date": (
                    str(current_date.year)
                    if month == 0
                    else current_date.strftime("%B")
                ),
                "summary_isk": total_amount["total"],
                "summary_ess": total_amount["ess"],
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
                        "day_isk": total_amount_day["total"],
                        "day_ess": total_amount_day["ess"],
                        "hourly_isk": total_amount_hour["total"],
                        "hourly_ess": total_amount_hour["ess"],
                    }
                )
            if stolen:
                day_stolen = round(stolen / current_date.day)
                hourly_stolen = round((stolen / current_date.day) / 24)

                summary.update(
                    {
                        "gain": gain,
                        "stolen": stolen,
                        "day_stolen_ess": stolen_day,
                        "day_stolen": day_stolen,
                        "hourly_stolen": hourly_stolen,
                    }
                )

            def _calculate_aggregates(
                total_amount,
                total_amount_day,
                total_amount_hour,
                summary_key,
                day_key,
                hour_key,
                overall_mode,
            ):  # pylint: disable=too-many-arguments
                summary.update(
                    {
                        summary_key: total_amount,
                        day_key: total_amount_day,
                        hour_key: total_amount_hour,
                        f"day_avg_{summary_key}": round(
                            total_amount / current_date.day
                        ),
                        f"hourly_avg_{summary_key}": round(
                            total_amount / (current_date.day * 24)
                        ),
                    }
                )
                if overall_mode or current_date.month != datetime.now().month:
                    summary.pop(day_key, 0)
                    summary.pop(hour_key, 0)

            if total_amount["mining"]:
                _calculate_aggregates(
                    total_amount["mining"],
                    total_amount_day["mining"],
                    total_amount_hour["mining"],
                    "mining",
                    "mining_day",
                    "mining_hour",
                    overall_mode,
                )

            if total_amount["transaction"]:
                _calculate_aggregates(
                    total_amount["transaction"],
                    total_amount_day["transaction"],
                    total_amount_hour["transaction"],
                    "trading",
                    "trading_day",
                    "trading_hour",
                    overall_mode,
                )

            if total_amount["contract"]:
                _calculate_aggregates(
                    total_amount["contract"],
                    total_amount_day["contract"],
                    total_amount_hour["contract"],
                    "contract",
                    "contract_day",
                    "contract_hour",
                    overall_mode,
                )

            if total_amount["production_cost"]:
                _calculate_aggregates(
                    total_amount["production_cost"],
                    total_amount_day["production_cost"],
                    total_amount_hour["production_cost"],
                    "production_cost",
                    "production_cost_day",
                    "production_cost_hour",
                    overall_mode,
                )

            if total_amount["market_cost"]:
                _calculate_aggregates(
                    total_amount["market_cost"],
                    total_amount_day["market_cost"],
                    total_amount_hour["market_cost"],
                    "trading_cost",
                    "trading_cost_day",
                    "trading_cost_hour",
                    overall_mode,
                )

            if total_amount["donation"]:
                _calculate_aggregates(
                    total_amount["donation"],
                    total_amount_day["donation"],
                    total_amount_hour["donation"],
                    "donation",
                    "donation_day",
                    "donation_hour",
                    overall_mode,
                )

            context = {"character": summary}

            return render(
                request, "ledger/modals/pve/view_character_content.html", context
            )
