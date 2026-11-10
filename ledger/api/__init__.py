# Third Party
from ninja import NinjaAPI
from ninja.security import django_auth

# Django
from django.conf import settings

# AA Ledger
from ledger.api import (
    administration,
    alliance,
    character,
    corporation,
    general,
    overview,
    planetary,
)
from ledger.providers import logger

api = NinjaAPI(
    title="Geuthur API",
    version="0.5.0",
    urls_namespace="ledger:api",
    auth=django_auth,
    openapi_url=settings.DEBUG and "/openapi.json" or "",
)


def setup(ninja_api):
    general.ApiEndpoints(ninja_api)
    overview.ApiEndpoints(ninja_api)
    administration.ApiEndpoints(ninja_api)

    # Character Endpoints
    character.ApiEndpoints(ninja_api)
    character.DetailsApiEndpoints(ninja_api)
    planetary.ApiEndpoints(ninja_api)

    # Corporation Endpoints
    corporation.ApiEndpoints(ninja_api)
    corporation.DetailsApiEndpoints(ninja_api)

    # Alliance Endpoints
    alliance.ApiEndpoints(ninja_api)
    alliance.DetailsApiEndpoints(ninja_api)


# Initialize API endpoints
setup(api)
