# AA Ledger
from ledger.models.characteraudit import CharacterMiningLedger, CharacterOwner


def create_miningledger(character: CharacterOwner, **kwargs) -> CharacterMiningLedger:
    """Create a CorporationWalletDivision"""
    params = {
        "character": character,
    }
    params.update(kwargs)
    division = CharacterMiningLedger(**params)
    division.save()
    return division
