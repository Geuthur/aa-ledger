"""App URLs"""

from django.urls import path, re_path

from ledger.api import api
from ledger.views.alliance import alliance_ledger
from ledger.views.alliance.add_ally import add_ally
from ledger.views.character import character_ledger, planetary
from ledger.views.character.add_char import add_char
from ledger.views.corporation import corp_events, corporation_ledger
from ledger.views.corporation.add_corp import add_corp

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
    path(
        "alliance_ledger/",
        alliance_ledger.alliance_ledger_index,
        name="alliance_ledger_index",
    ),
    path(
        "alliance_ledger/<int:alliance_id>/",
        alliance_ledger.alliance_ledger,
        name="alliance_ledger",
    ),
    path(
        "alliance_ledger/<int:alliance_id>/view/administration/",
        alliance_ledger.alliance_administration,
        name="alliance_administration",
    ),
    path(
        "alliance_overview/",
        alliance_ledger.alliance_overview,
        name="alliance_overview",
    ),
    path("alliance/add/", add_ally, name="add_ally"),
    # -- -- Corporation Ledger
    path(
        "corporation_ledger/",
        corporation_ledger.corporation_ledger_index,
        name="corporation_ledger_index",
    ),
    path(
        "corporation_ledger/<int:corporation_id>/",
        corporation_ledger.corporation_ledger,
        name="corporation_ledger",
    ),
    path(
        "corporation_ledger/<int:corporation_id>/view/administration/",
        corporation_ledger.corporation_administration,
        name="corporation_administration",
    ),
    path(
        "corporation_overview/",
        corporation_ledger.corporation_overview,
        name="corporation_overview",
    ),
    # -- -- Character Ledger
    path(
        "character_ledger/",
        character_ledger.character_ledger_index,
        name="character_ledger_index",
    ),
    path(
        "character_ledger/<int:character_id>/",
        character_ledger.character_ledger,
        name="character_ledger",
    ),
    path(
        "character_ledger/<int:character_id>/view/administration/",
        character_ledger.character_administration,
        name="character_administration",
    ),
    path(
        "character_overview/",
        character_ledger.character_overview,
        name="character_overview",
    ),
    # -- -- Events
    path("events/", corp_events.events_index, name="events_index"),
    path("events/admin/", corp_events.events_admin, name="event_admin"),
    path("events/create/", corp_events.create_event, name="create_event"),
    path("events/<int:event_id>/edit/", corp_events.edit_event, name="edit_event"),
    path(
        "events/<int:event_id>/delete/", corp_events.delete_event, name="delete_event"
    ),
    path("events/ajax/load_events", corp_events.load_events, name="load_events"),
    # -- -- Planetary
    path(
        "planetary_ledger/",
        planetary.planetary_ledger_index,
        name="planetary_ledger_index",
    ),
    path(
        "planetary_ledger/<int:character_id>/",
        planetary.planetary_ledger,
        name="planetary_ledger",
    ),
    path(
        "planetary/switch_alarm/<int:character_id>/planet/<int:planet_id>/",
        planetary.switch_alarm,
        name="switch_alarm",
    ),
    path(
        "planetary_overview/", planetary.planetary_overview, name="planetary_overview"
    ),
    # -- API System
    re_path(r"^api/", api.urls),
]
