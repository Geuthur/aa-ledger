from .admin import LedgerAdminApiEndpoints
from .ledger import LedgerApiEndpoints
from .planetary import LedgerPlanetaryApiEndpoints


def setup(api):
    LedgerAdminApiEndpoints(api)
    LedgerApiEndpoints(api)
    LedgerPlanetaryApiEndpoints(api)
