"""App URLs"""

from django.urls import path, re_path

from ledger.api import api
from ledger.views.alliance.alliance_ledger import alliance_admin, alliance_ledger
from ledger.views.alliance.ally_audit import add_ally
from ledger.views.character.char_audit import add_char
from ledger.views.character.character_ledger import character_admin, character_ledger
from ledger.views.character.planetary import (
    planetary_admin,
    planetary_ledger,
    switch_alarm,
)
from ledger.views.corporation.corp_audit import add_corp
from ledger.views.corporation.corp_events import (
    create_event,
    delete_event,
    edit_event,
    events_admin,
    events_index,
    load_events,
)
from ledger.views.corporation.corporation_ledger import (
    corporation_admin,
    corporation_ledger,
)

# AA Example App
from ledger.views.pve import ledger_index

app_name: str = "ledger"

urlpatterns = [
    path("", ledger_index, name="index"),
    # -- Character Audit
    path("char/add/", add_char, name="ledger_add_char"),
    # -- Corporation Audit
    path("corporation/add/", add_corp, name="ledger_add_corp"),
    # -- PvE
    path("index", ledger_index, name="ledger_index"),
    # -- -- Alliance Ledger
    path(
        "alliance_ledger/<int:alliance_pk>/",
        alliance_ledger,
        name="alliance_ledger",
    ),
    path("alliance_admin/", alliance_admin, name="alliance_admin"),
    path("alliance/add/", add_ally, name="ledger_add_ally"),
    # -- -- Corporation Ledger
    path(
        "corporation_ledger/<int:corporation_pk>/",
        corporation_ledger,
        name="corporation_ledger",
    ),
    path("corporation_admin/", corporation_admin, name="corporation_admin"),
    # -- -- Char Ledger
    path(
        "character_ledger/<int:character_pk>/",
        character_ledger,
        name="character_ledger",
    ),
    path("character_admin/", character_admin, name="character_admin"),
    # -- -- Events
    path("events/", events_index, name="events_index"),
    path("events/admin/", events_admin, name="event_admin"),
    path("events/create/", create_event, name="create_event"),
    path("events/<int:event_id>/edit/", edit_event, name="edit_event"),
    path("events/<int:event_id>/delete/", delete_event, name="delete_event"),
    path("events/ajax/load_events", load_events, name="load_events"),
    # -- -- Planetary
    path(
        "planetary_ledger/<int:character_pk>/",
        planetary_ledger,
        name="planetary_ledger",
    ),
    path(
        "planetary/switch_alarm/<int:character_id>/planet/<int:planet_id>/",
        switch_alarm,
        name="switch_alarm",
    ),
    path("planetary_admin/", planetary_admin, name="planetary_admin"),
    # -- API System
    re_path(r"^api/", api.urls),
]
