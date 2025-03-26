import logging
from datetime import datetime

from django.db.models import Q

from allianceauth.eveonline.models import EveAllianceInfo

from ledger.api.api_helper.billboard_helper import BillboardAlliance
from ledger.api.api_helper.core_manager import LedgerTotal
from ledger.models.corporationaudit import (
    CorporationWalletJournalEntry,
)

logger = logging.getLogger(__name__)


# pylint: disable=duplicate-code
class AllianceProcess:
    """JournalProcess class to process the journal entries."""

    def __init__(self, alliance: EveAllianceInfo, date: datetime, view=None):
        self.alliance = alliance
        self.date = date
        self.view = view

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
        alliance_dict = {}
        alliance_total = LedgerTotal()

        ledger_journal = (
            journal.values(  # Convert the queryset into dictionaries
                "division__corporation__corporation__corporation_id",
                "division__corporation__corporation__corporation_name",
            )
            .annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
            .annotate_daily_goal_income()
        )

        for corporation in ledger_journal:
            total_bounty = corporation.get("bounty_income", 0)
            total_ess = corporation.get("ess_income", 0)
            total_other = corporation.get("miscellaneous", 0)
            corporation_id = corporation.get(
                "division__corporation__corporation__corporation_id", 0
            )
            corporation_name = (
                corporation.get("division__corporation__corporation__corporation_name")
                or "Unknown"
            )
            summary_amount = sum([total_bounty, total_ess, total_other])

            if summary_amount > 0:
                alliance_dict[corporation_id] = {
                    "main_id": corporation_id,
                    "main_name": corporation_name,
                    "entity_type": "corporation",
                    "alt_names": [],
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
            alliance_total.get_summary(totals)

        return alliance_dict, alliance_total

    def generate_ledger(self):
        # Get the Filter Settings
        filter_date = self._filter_date()

        journal = (
            CorporationWalletJournalEntry.objects.filter(filter_date)
            .select_related(
                "first_party",
                "second_party",
            )
            .generate_ledger_alliance(self.alliance.alliance_id)
        )

        # Create the Billboard for the Corporation
        billboard = BillboardAlliance(view=self.view, journal=journal)
        billboard_dict = billboard.billboard_ledger()

        # Create the Dicts for each Character
        alliance_dict, alliance_total = self._process_corporation_chars(journal)

        output = []
        output.append(
            {
                "ratting": sorted(
                    list(alliance_dict.values()), key=lambda x: x["main_name"]
                ),
                "billboard": billboard_dict,
                "total": alliance_total.to_dict(),
            }
        )

        return output
