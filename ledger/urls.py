"""App URLs"""

# Django
from django.urls import path, re_path

# AA Ledger
from ledger.api import api
from ledger.views import add_ally, add_char, add_corp, react_base

app_name: str = "ledger"  # pylint: disable=invalid-name

urlpatterns = [
    # -- Registration via ESI SSO (server-side)
    path("character/add/", add_char, name="add_char"),
    path("corporation/add/", add_corp, name="add_corp"),
    path("alliance/add/", add_ally, name="add_ally"),
    # -- API System
    re_path(r"^api/", api.urls),
    # -- React Frontend, all other routes are handled by the router
    path("", react_base, name="index"),
    re_path(r"^(?!api/).*$", react_base, name="react_base"),
]
