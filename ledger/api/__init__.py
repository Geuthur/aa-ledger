import logging

from ninja import NinjaAPI
from ninja.security import django_auth

from django.conf import settings

from ledger.api import ledger

logger = logging.getLogger(__name__)

api = NinjaAPI(
    title="Geuthur API",
    version="0.1.0",
    urls_namespace="ledger:new_api",
    auth=django_auth,
    csrf=True,
    openapi_url=settings.DEBUG and "/openapi.json" or "",
)

# Add the ledger endpoints
ledger.setup(api)
