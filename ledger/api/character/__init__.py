from .journal import LedgerJournalApiEndpoints
from .ledger import LedgerApiEndpoints
from .template import LedgerTemplateApiEndpoints


def setup(api):
    LedgerApiEndpoints(api)
    LedgerTemplateApiEndpoints(api)
    LedgerJournalApiEndpoints(api)
