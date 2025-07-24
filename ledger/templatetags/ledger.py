# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__, __version__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)
