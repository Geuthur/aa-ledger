from .admin import LedgerAdminApiEndpoints
from .planetary import LedgerPlanetaryApiEndpoints


def setup(api):
    LedgerAdminApiEndpoints(api)
    LedgerPlanetaryApiEndpoints(api)
