# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# Alliance Auth (External Libs)
from app_utils.testing import (
    create_user_from_evecharacter,
)

# AA Ledger
from ledger.models.characteraudit import CharacterWalletJournalEntry
from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
)


def create_division(
    corporation: CorporationAudit, **kwargs
) -> CorporationWalletDivision:
    """Create a CorporationWalletDivision"""
    params = {
        "corporation": corporation,
    }
    params.update(kwargs)
    division = CorporationWalletDivision(**params)
    division.save()
    return division


def create_wallet_journal_entry(
    journal_type: str, **kwargs
) -> CorporationWalletJournalEntry | CharacterWalletJournalEntry:
    """Create a CorporationWalletJournalEntry"""
    params = {}
    params.update(kwargs)
    if journal_type == "corporation":
        journal_entry = CorporationWalletJournalEntry(**params)
    else:
        journal_entry = CharacterWalletJournalEntry(**params)
    journal_entry.save()
    return journal_entry
