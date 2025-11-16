"""Initialize the app"""

__version__ = "1.0.3"
__title__ = "Ledger"

__package_name__ = "aa-ledger"
__app_name__ = "ledger"
__esi_compatibility_date__ = "2025-11-06"
__app_name_useragent__ = "AA-Ledger"

__github_url__ = f"https://github.com/Geuthur/{__package_name__}"

__character_operations__ = [
    "GetCharactersCharacterIdWalletJournal",
    "GetCharactersCharacterIdRoles",
    "GetCharactersCharacterIdPlanets",
    "GetCharactersCharacterIdPlanetsPlanetId",
    "GetCharactersCharacterIdMining",
]

__corporation_operations__ = [
    "GetCorporationsCorporationIdWallets",
    "GetCorporationsCorporationIdWalletsDivisionJournal",
    "GetCorporationsCorporationIdDivisions",
]

__universe_operations__ = ["PostUniverseNames"]
