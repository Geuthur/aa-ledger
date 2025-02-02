from datetime import datetime

from django.db.models import Q

from ledger.api.api_helper.billboard_helper import BillboardLedger
from ledger.api.api_helper.core_manager import LedgerModels, LedgerTotal
from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import CorporationWalletJournalEntry

logger = get_extension_logger(__name__)


class CorporationProcess:
    """JournalProcess class to process the journal entries."""

    def __init__(self, corporations, date: datetime, view=None):
        self.corp = corporations if corporations else []
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
        corporation_dict = {}
        corporation_total = LedgerTotal()

        # Annotate Data
        journal = (
            journal.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
        )
        for main in journal:
            total_bounty = main.get("bounty_income") or 0
            total_ess = main.get("ess_income") or 0
            total_other = main.get("miscellaneous") or 0
            main_entity_id = main.get("main_entity_id") or 0
            character_name = main.get("main_entity_name") or "Unknown"
            alts = main.get("alts", [])
            entity_type = "character"

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
            CorporationWalletJournalEntry.objects.filter(filter_date)
            .select_related(
                "first_party",
                "second_party",
            )
            .generate_ledger(self.corp)
        )

        # Create the Dicts for each Character
        corporation_dict, corporation_total = self._process_corporation_chars(journal)

        output = []
        output.append(
            {
                "ratting": sorted(
                    list(corporation_dict.values()), key=lambda x: x["main_name"]
                ),
                "total": corporation_total.to_dict(),
            }
        )

        return output

    def generate_billboard(self, corporations):
        # Get the Filter Settings
        filter_date = self._filter_date()

        corporation_journal = (
            CorporationWalletJournalEntry.objects.filter(filter_date)
            .select_related(
                "first_party",
                "second_party",
            )
            .generate_ledger(corporations)
        )

        chars_list = list(corporation_journal.values_list("second_party_id", flat=True))

        models = LedgerModels(corporation_journal=corporation_journal)

        # Create the Billboard for the Corporation
        ledger = BillboardLedger(view=self.view, models=models, corp=True)

        billboard_dict = ledger.billboard_ledger(chars_list)

        output = []
        output.append(
            {
                "billboard": billboard_dict,
            }
        )

        return output
