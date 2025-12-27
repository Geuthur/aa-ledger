# Third Party
from ninja import NinjaAPI
from ninja.security import django_auth

# Django
from django.conf import settings

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.api import admin, planetary
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


api = NinjaAPI(
    title="Geuthur API",
    version="0.5.0",
    urls_namespace="ledger:api",
    auth=django_auth,
    openapi_url=settings.DEBUG and "/openapi.json" or "",
)


def setup(ninja_api):
    admin.AdminApiEndpoints(ninja_api)
    planetary.PlanetaryApiEndpoints(ninja_api)


# Initialize API endpoints
setup(api)
