"""Initialize the app"""

__version__ = "2.0.0"
__title__ = "Ledger"

__package_name__ = "aa-ledger"
__app_name__ = "ledger"
__esi_compatibility_date__ = "2025-12-16"
__app_name_useragent__ = "AA-Ledger"

__github_url__ = f"https://github.com/Geuthur/{__package_name__}"

__operations__ = [
    "GetCharactersCharacterIdWalletJournal",
    "GetCharactersCharacterIdRoles",
    "GetCharactersCharacterIdPlanets",
    "GetCharactersCharacterIdPlanetsPlanetId",
    "GetCharactersCharacterIdMining",
    # Market
    "GetMarketsPrices",
    # Corporation
    "GetCorporationsCorporationIdWallets",
    "GetCorporationsCorporationIdWalletsDivisionJournal",
    "GetCorporationsCorporationIdDivisions",
    # Universe
    "PostUniverseNames",
]
