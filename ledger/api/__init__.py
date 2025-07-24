# Third Party
from ninja import NinjaAPI
from ninja.security import django_auth

# Django
from django.conf import settings

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.api import ledger

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


api = NinjaAPI(
    title="Geuthur API",
    version="0.5.0",
    urls_namespace="ledger:api",
    auth=django_auth,
    csrf=True,
    openapi_url=settings.DEBUG and "/openapi.json" or "",
)

# Add the ledger endpoints
ledger.setup(api)
