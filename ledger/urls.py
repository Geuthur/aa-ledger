"""App URLs"""

from django.urls import path, re_path

from ledger.api import api
from ledger.views.alliance.add_ally import add_ally
from ledger.views.alliance.alliance_ledger import (
    alliance_ledger,
    alliance_ledger_index,
    alliance_overview,
)
from ledger.views.character.add_char import add_char
from ledger.views.character.character_ledger import (
    character_ledger,
    character_ledger_index,
    character_overview,
)
from ledger.views.character.planetary import (
    planetary_ledger,
    planetary_ledger_index,
    planetary_overview,
    switch_alarm,
)
from ledger.views.corporation.add_corp import add_corp
from ledger.views.corporation.corp_events import (
    create_event,
    delete_event,
    edit_event,
    events_admin,
    events_index,
    load_events,
)
from ledger.views.corporation.corporation_ledger import (
    corporation_ledger,
    corporation_ledger_index,
    corporation_overview,
)

# AA Example App
from ledger.views.index import index

app_name: str = "ledger"

urlpatterns = [
    path("", index, name="index"),
    # -- Character Audit
    path("char/add/", add_char, name="add_char"),
    # -- Corporation Audit
    path("corporation/add/", add_corp, name="add_corp"),
    # -- -- Alliance Ledger
    path("alliance_ledger/", alliance_ledger_index, name="alliance_ledger_index"),
    path(
        "alliance_ledger/<int:alliance_id>/",
        alliance_ledger,
        name="alliance_ledger",
    ),
    path("alliance_overview/", alliance_overview, name="alliance_overview"),
    path("alliance/add/", add_ally, name="add_ally"),
    # -- -- Corporation Ledger
    path(
        "corporation_ledger/", corporation_ledger_index, name="corporation_ledger_index"
    ),
    path(
        "corporation_ledger/<int:corporation_id>/",
        corporation_ledger,
        name="corporation_ledger",
    ),
    path("corporation_overview/", corporation_overview, name="corporation_overview"),
    # -- -- Character Ledger
    path("character_ledger/", character_ledger_index, name="character_ledger_index"),
    path(
        "character_ledger/<int:character_id>/",
        character_ledger,
        name="character_ledger",
    ),
    path("character_overview/", character_overview, name="character_overview"),
    # -- -- Events
    path("events/", events_index, name="events_index"),
    path("events/admin/", events_admin, name="event_admin"),
    path("events/create/", create_event, name="create_event"),
    path("events/<int:event_id>/edit/", edit_event, name="edit_event"),
    path("events/<int:event_id>/delete/", delete_event, name="delete_event"),
    path("events/ajax/load_events", load_events, name="load_events"),
    # -- -- Planetary
    path("planetary_ledger/", planetary_ledger_index, name="planetary_ledger_index"),
    path(
        "planetary_ledger/<int:character_id>/",
        planetary_ledger,
        name="planetary_ledger",
    ),
    path(
        "planetary/switch_alarm/<int:character_id>/planet/<int:planet_id>/",
        switch_alarm,
        name="switch_alarm",
    ),
    path("planetary_overview/", planetary_overview, name="planetary_overview"),
    # -- API System
    re_path(r"^api/", api.urls),
]
