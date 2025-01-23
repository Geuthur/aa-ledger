from django.db.models import Q

from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)

from ledger.api.api_helper.billboard_helper import BillboardData, BillboardLedger
from ledger.api.api_helper.core_manager import LedgerDate, LedgerModels, LedgerTotal
from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import CorporationWalletJournalEntry
from ledger.tasks import create_missing_entitys

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
        unkwowns_ids = set()

        for main in journal:
            total_bounty = main.get("total_bounty", 0)
            total_ess = main.get("total_ess", 0)
            total_other = main.get("total_miscellaneous", 0)
            main_entity_id = main.get("main_entity_id", 0)
            alts = main.get("alts", [])
            character_name = "Unknown"
            entity_type = "character"

            if not main_entity_id == 0 and main_entity_id is not None:
                # logger.info("Processing: %s", main_entity_id)
                try:
                    character_name = EveCharacter.objects.get(
                        character_id=main_entity_id
                    ).character_name
                except EveCharacter.DoesNotExist:
                    try:
                        character_name = EveCorporationInfo.objects.get(
                            corporation_id=main_entity_id
                        ).corporation_name
                        entity_type = "corporation"
                    except EveCorporationInfo.DoesNotExist:
                        try:
                            character_name = EveAllianceInfo.objects.get(
                                alliance_id=main_entity_id
                            ).alliance_name
                            entity_type = "alliance"
                        except EveAllianceInfo.DoesNotExist:
                            unkwowns_ids.add(main_entity_id)
                            continue

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

        # Create Unknown Characters
        if unkwowns_ids:
            create_missing_entitys.apply_async(args=[list(unkwowns_ids)], priority=6)

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
