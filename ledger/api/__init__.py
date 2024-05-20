from ninja import NinjaAPI
from ninja.security import django_auth

from django.conf import settings

from ledger.api import character, corporation
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)

api = NinjaAPI(
    title="Geuthur API",
    version="0.1.0",
    urls_namespace="ledger:new_api",
    auth=django_auth,
    csrf=True,
    openapi_url=settings.DEBUG and "/openapi.json" or "",
)

# Add the character endpoints
character.setup(api)

# Add the corporation endpoints
corporation.setup(api)
