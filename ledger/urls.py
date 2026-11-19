"""App URLs"""

# Django
from django.urls import path, re_path

# Alliance Auth
from allianceauth.authentication.decorators import decorate_url_patterns

# AA Ledger
from ledger.api import api
from ledger.api.auth import basic_access_required
from ledger.views import add_ally, add_char, add_corp, react_base

app_name: str = "ledger"  # pylint: disable=invalid-name

# Every URL of the API (endpoints, schema and docs) requires `basic_access`
api_patterns, api_app_name, api_namespace = api.urls
api_patterns = decorate_url_patterns(
    (api_patterns, api_app_name), basic_access_required
)[0]

urlpatterns = [
    # -- Registration via ESI SSO (server-side)
    path("character/add/", add_char, name="add_char"),
    path("corporation/add/", add_corp, name="add_corp"),
    path("alliance/add/", add_ally, name="add_ally"),
    # -- API System
    re_path(r"^api/", (api_patterns, api_app_name, api_namespace)),
    # -- React Frontend, all other routes are handled by the router
    path("", react_base, name="index"),
    re_path(r"^(?!api/).*$", react_base, name="react_base"),
]
