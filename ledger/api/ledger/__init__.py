from .admin import LedgerAdminApiEndpoints
from .ledger import LedgerApiEndpoints
from .planetary import LedgerPlanetaryApiEndpoints
from .template import LedgerTemplateApiEndpoints


def setup(api):
    LedgerAdminApiEndpoints(api)
    LedgerApiEndpoints(api)
    LedgerPlanetaryApiEndpoints(api)
    LedgerTemplateApiEndpoints(api)
