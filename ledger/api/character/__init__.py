from .journal import LedgerJournalApiEndpoints
from .ledger import LedgerApiEndpoints
from .planetary import LedgerPlanetaryApiEndpoints
from .template import LedgerTemplateApiEndpoints


def setup(api):
    LedgerApiEndpoints(api)
    LedgerTemplateApiEndpoints(api)
    LedgerJournalApiEndpoints(api)
    LedgerPlanetaryApiEndpoints(api)
