"""App URLs"""

from django.urls import path, re_path

from ledger.api import api
from ledger.views.character.char_audit import add_char, fetch_memberaudit
from ledger.views.corporation.corp_audit import add_corp
from ledger.views.corporation.corp_events import (
    create_event,
    delete_event,
    edit_event,
    events_admin,
    events_index,
    load_events,
)
from ledger.views.corporation.corp_tax import index_steuer

# AA Example App
from ledger.views.pve import ledger_index, ratting_char_index, ratting_index

app_name: str = "ledger"

urlpatterns = [
    path("", ledger_index, name="index"),
    # -- Character Audit
    path("char/add/", add_char, name="ledger_add_char"),
    re_path(
        r"^char/fetch_memberaudit/", fetch_memberaudit, name="ledger_fetch_memberaudit"
    ),
    # -- Corporation Audit
    path("corporation/add/", add_corp, name="ledger_add_corp"),
    # -- PvE
    path("index", ledger_index, name="ledger_index"),
    # -- -- Steuer
    path("steuer/index", index_steuer, name="steuer_index"),
    # -- -- Corporation Ledger
    path("corp_index", ratting_index, name="ledger_corp_index"),
    # -- -- Char Ledger
    path("char_index", ratting_char_index, name="ledger_char_index"),
    # -- -- Events
    path("events/", events_index, name="events_index"),
    path("events/admin/", events_admin, name="event_admin"),
    path("events/create/", create_event, name="create_event"),
    path("events/<int:event_id>/edit/", edit_event, name="edit_event"),
    path("events/<int:event_id>/delete/", delete_event, name="delete_event"),
    path("events/ajax/load_events", load_events, name="load_events"),
    # -- API System
    re_path(r"^api/", api.urls),
]
