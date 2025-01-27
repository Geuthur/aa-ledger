from django.db.models import Q

from ledger.api.api_helper.billboard_helper import BillboardData, BillboardLedger
from ledger.api.api_helper.core_manager import LedgerDate, LedgerModels, LedgerTotal
from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import CorporationWalletJournalEntry
from ledger.models.general import EveEntity

logger = get_extension_logger(__name__)


class CorporationProcess:
    """JournalProcess class to process the journal entries."""

    def __init__(self, corporations, year, month):
        self.corp = corporations if corporations else []
        self.year = year
        self.month = month

    # pylint: disable=too-many-locals
    def _process_corporation_chars(self, journal):
        # Create the Dicts for each Character
        corporation_dict = {}
        corporation_total = LedgerTotal()

        for main in journal:
            total_bounty = main.get("bounty", 0)
            total_ess = main.get("ess", 0)
            total_other = main.get("miscellaneous", 0)
            main_entity_id = main.get("main_entity_id", 0)
            alts = main.get("alts", [])
            character_name = "Unknown"
            entity_type = "character"

            if not main_entity_id == 0 and main_entity_id is not None:
                try:
                    character_name = EveEntity.objects.get(eve_id=main_entity_id).name
                    entity_type = EveEntity.objects.get(eve_id=main_entity_id).category
                except EveEntity.DoesNotExist:
                    pass

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
        filter_date = Q(date__year=self.year)
        if not self.month == 0:
            filter_date &= Q(date__month=self.month)

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
        filter_date = Q(date__year=self.year)
        if not self.month == 0:
            filter_date &= Q(date__month=self.month)

        corporation_journal = (
            CorporationWalletJournalEntry.objects.filter(filter_date)
            .select_related(
                "first_party",
                "second_party",
            )
            .generate_ledger(corporations)
        )

        # Create the Dicts for each Character
        corporation_dict, corporation_total = self._process_corporation_chars(
            corporation_journal
        )

        chars_list = list(corporation_journal.values_list("second_party_id", flat=True))

        # Create Data for Billboard
        date_data = LedgerDate(self.year, self.month)
        data = BillboardData(
            corporation_dict=corporation_dict,
            total_amount=corporation_total.total_amount,
        )
        models = LedgerModels(corporation_journal=corporation_journal)

        # Create the Billboard for the Corporation
        ledger = BillboardLedger(date_data, models, data, corp=True)

        billboard_dict = ledger.billboard_corp_ledger(chars_list)

        output = []
        output.append(
            {
                "billboard": billboard_dict,
            }
        )

        return output
