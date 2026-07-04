# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models

# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.helpers.billboard import BillboardSystem
from ledger.models.characteraudit import (
    CharacterMiningLedger,
    CharacterOwner,
    CharacterWalletJournalEntry,
)
from ledger.models.corporationaudit import CorporationOwner
from ledger.providers import AppLogger

if TYPE_CHECKING:
    # AA Ledger
    from ledger.models.ledger import (
        CharacterLedgerEntry,
    )

logger = AppLogger(get_extension_logger(__name__), __title__)


class BillboardEntryQueryset(models.QuerySet["CharacterLedgerEntry"]):
    pass


class BillboardEntryManager(models.Manager["CharacterLedgerEntry"]):
    def get_queryset(self) -> BillboardEntryQueryset:
        return BillboardEntryQueryset(self.model, using=self._db)

    def update_or_create_billboard_entry(
        self,
        owner: CharacterOwner | CorporationOwner | EveAllianceInfo,
        request_info: dict,
        wallet_journal: CharacterWalletJournalEntry,
        ledger_list: list,
        mining_journal: CharacterMiningLedger | None = None,
    ) -> None:
        """
        Update or create the billboard entry for the given owner based on the most recent ledger entry.

        Args:
            owner (CharacterOwner | CorporationOwner | EveAllianceInfo): The owner for whom the billboard entry is being updated or created.
            request_info (dict): Information about the request, including year, month, day, and whether it's final data.
            wallet_journal (CharacterWalletJournalEntry): The wallet journal entry to be used for generating the billboard data.
            ledger_list (list): A list of ledger entries to be used for generating the chord billboard.
            mining_journal (CharacterMiningLedger, optional): The mining journal entry to be used for generating the billboard data. Defaults to None.
        Returns:
            None
        """
        billoard_system = BillboardSystem()

        wallet_timeline = (
            billoard_system.create_timeline(
                journal=wallet_journal, request_info=request_info
            )
            .annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
        )

        # Generate XY Billboard
        xy_results = billoard_system.create_or_update_results(wallet_timeline)

        # Add mining data to XY Billboard if available
        if mining_journal:
            mining_timeline = billoard_system.create_timeline(
                journal=mining_journal, request_info=request_info
            ).annotate_mining(with_period=True)
            xy_results = billoard_system.add_category_to_xy_billboard(
                xy_results, category="mining", queryset=mining_timeline
            )

        xy_billboard = billoard_system.create_xy_billboard(
            results=xy_results, request_info=request_info
        )
        # Initialize Chord Billboard
        chord_billboard = billoard_system.create_chord_billboard(ledger_list)

        if not xy_billboard or not chord_billboard:
            return

        # Determine the name for the billboard entry based on the owner type
        if isinstance(owner, CharacterOwner):
            name = owner.eve_character.character_name
        elif isinstance(owner, CorporationOwner):
            name = owner.eve_corporation.corporation_name
        elif isinstance(owner, EveAllianceInfo):
            name = owner.alliance_name
        else:
            raise ValueError("Invalid owner type for billboard entry")

        # Update or create the billboard entry for the character
        self.update_or_create(
            owner=owner,
            year=request_info.year,
            month=request_info.month,
            day=request_info.day,
            defaults={
                "name": name,
                "xy_billboard": xy_billboard.asdict(),
                "chord_billboard": chord_billboard.asdict(),
                "final_data": request_info.is_final_data,
            },
        )
