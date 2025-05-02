# Standard Library
import logging

# Third Party
from ninja import NinjaAPI
from ninja.security import django_auth

# Django
from django.conf import settings

# AA Ledger
from ledger.api import ledger

logger = logging.getLogger(__name__)

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
