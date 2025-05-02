# AA Ledger
from ledger.models.characteraudit import CharacterAudit, CharacterMiningLedger


def create_miningledger(character: CharacterAudit, **kwargs) -> CharacterMiningLedger:
    """Create a CorporationWalletDivision"""
    params = {
        "character": character,
    }
    params.update(kwargs)
    division = CharacterMiningLedger(**params)
    division.save()
    return division
