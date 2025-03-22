from datetime import datetime

from django.db.models import Q

from ledger.api.api_helper.billboard_helper import BillboardCorporation
from ledger.api.api_helper.core_manager import LedgerTotal
from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletJournalEntry,
)

logger = get_extension_logger(__name__)


class CorporationProcess:
    """JournalProcess class to process the journal entries."""

    def __init__(self, corporation: CorporationAudit, date: datetime, view=None):
        self.corporation = corporation
        self.date = date
        self.view = view

    # pylint: disable=duplicate-code
    def _filter_date(self):
        """Filter the date."""
        filter_date = Q(date__year=self.date.year)
        if self.view == "month":
            filter_date &= Q(date__month=self.date.month)
        elif self.view == "day":
            filter_date &= Q(date__month=self.date.month)
            filter_date &= Q(date__day=self.date.day)
        return filter_date

    # pylint: disable=too-many-locals
    def _process_corporation_chars(self, journal):
        # Create the Dicts for each Character
        corporation_dict = {}
        corporation_total = LedgerTotal()

        # Annotate Data
        ledger_journal = (
            journal.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
            .annotate_daily_goal_income()
        )

        for main in ledger_journal:
            total_bounty = main.get("bounty_income", 0)
            total_ess = main.get("ess_income", 0)
            total_other = main.get("miscellaneous", 0)
            main_entity_id = main.get("main_entity_id", 0)
            entity_type = main.get("main_entity_type", "character")
            character_name = main.get("main_entity_name") or "Unknown"
            alts = main.get("alts", [])

            summary_amount = sum([total_bounty, total_ess, total_other])

            if summary_amount > 0:
                corporation_dict[main_entity_id] = {
                    "main_id": main_entity_id,
                    "main_name": character_name,
                    "entity_type": entity_type,
                    "alt_names": alts,
                    "total_amount": total_bounty,
                    "total_amount_ess": total_ess,
                    "total_amount_others": total_other,
                }

            totals = {
                "total_amount": total_bounty,
                "total_amount_ess": total_ess,
                "total_amount_others": total_other,
                "total_amount_all": summary_amount,
            }
            # Summary all
            corporation_total.get_summary(totals)

        return corporation_dict, corporation_total

    def generate_ledger(self):
        # Get the Filter Settings
        filter_date = self._filter_date()

        journal = (
            CorporationWalletJournalEntry.objects.filter(
                filter_date,
                division__corporation__corporation__corporation_id=self.corporation.corporation.corporation_id,
            )
            .select_related(
                "first_party",
                "second_party",
            )
            .generate_ledger()
        )

        # Create the Billboard for the Corporation
        billboard = BillboardCorporation(view=self.view, journal=journal)
        billboard_dict = billboard.billboard_ledger()

        # Create the Dicts for each Character
        corporation_dict, corporation_total = self._process_corporation_chars(journal)

        output = []
        output.append(
            {
                "ratting": sorted(
                    list(corporation_dict.values()), key=lambda x: x["main_name"]
                ),
                "billboard": billboard_dict,
                "total": corporation_total.to_dict(),
            }
        )

        return output
