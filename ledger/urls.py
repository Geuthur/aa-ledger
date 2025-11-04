"""App URLs"""

# Django
from django.urls import path, re_path

# AA Ledger
from ledger.api import api
from ledger.views.alliance import alliance_ledger
from ledger.views.alliance.add_ally import add_ally
from ledger.views.character import character_ledger, planetary
from ledger.views.character.add_char import add_char
from ledger.views.corporation import corporation_ledger
from ledger.views.corporation.add_corp import add_corp

# AA Example App
from ledger.views.index import admin, index

app_name: str = "ledger"  # pylint: disable=invalid-name

urlpatterns = [
    path("", index, name="index"),
    path("admin/", admin, name="admin"),
    # -- Character Audit
    path("character/add/", add_char, name="add_char"),
    path(
        "character/delete/<int:character_id>/",
        character_ledger.character_delete,
        name="delete_char",
    ),
    # -- Corporation Audit
    path("corporation/add/", add_corp, name="add_corp"),
    path(
        "corporation/delete/<int:corporation_id>/",
        corporation_ledger.corporation_delete,
        name="delete_corp",
    ),
    # -- -- Alliance Ledger
    path(
        "alliance/",
        alliance_ledger.alliance_ledger_index,
        name="alliance_ledger_index",
    ),
    path(
        "alliance/<int:alliance_id>/",
        alliance_ledger.alliance_ledger,
        name="alliance_ledger",
    ),
    path(
        "alliance/<int:alliance_id>/date/<int:year>/",
        alliance_ledger.alliance_ledger,
        name="alliance_ledger",
    ),
    path(
        "alliance/<int:alliance_id>/date/<int:year>/<int:month>/",
        alliance_ledger.alliance_ledger,
        name="alliance_ledger",
    ),
    path(
        "alliance/<int:alliance_id>/date/<int:year>/<int:month>/<int:day>/",
        alliance_ledger.alliance_ledger,
        name="alliance_ledger",
    ),
    # -- -- Alliance Details
    path(
        "alliance/<int:alliance_id>/view/details/<int:entity_id>/section/<str:section>/",
        alliance_ledger.alliance_details,
        name="alliance_details",
    ),
    path(
        "alliance/<int:alliance_id>/<int:year>/view/details/<int:entity_id>/section/<str:section>/",
        alliance_ledger.alliance_details,
        name="alliance_details",
    ),
    path(
        "alliance/<int:alliance_id>/<int:year>/<int:month>/view/details/<int:entity_id>/section/<str:section>/",
        alliance_ledger.alliance_details,
        name="alliance_details",
    ),
    path(
        "alliance/<int:alliance_id>/<int:year>/<int:month>/<int:day>/view/details/<int:entity_id>/section/<str:section>/",
        alliance_ledger.alliance_details,
        name="alliance_details",
    ),
    path(
        "alliance/<int:alliance_id>/<int:year>/<int:month>/<int:day>/view/details/<int:entity_id>/section/<str:section>/",
        alliance_ledger.alliance_details,
        name="alliance_details",
    ),
    path(
        "alliance/<int:alliance_id>/view/administration/",
        alliance_ledger.alliance_administration,
        name="alliance_administration",
    ),
    path(
        "alliance/view/overview/",
        alliance_ledger.alliance_overview,
        name="alliance_overview",
    ),
    path("alliance/add/", add_ally, name="add_ally"),
    # -- -- Corporation Ledger
    path(
        "corporation/",
        corporation_ledger.corporation_ledger_index,
        name="corporation_ledger_index",
    ),
    path(
        "corporation/<int:corporation_id>/",
        corporation_ledger.corporation_ledger,
        name="corporation_ledger",
    ),
    path(
        "corporation/<int:corporation_id>/date/<int:year>/",
        corporation_ledger.corporation_ledger,
        name="corporation_ledger",
    ),
    path(
        "corporation/<int:corporation_id>/date/<int:year>/<int:month>/",
        corporation_ledger.corporation_ledger,
        name="corporation_ledger",
    ),
    path(
        "corporation/<int:corporation_id>/date/<int:year>/<int:month>/<int:day>/",
        corporation_ledger.corporation_ledger,
        name="corporation_ledger",
    ),
    path(
        "corporation/<int:corporation_id>/division/<int:division_id>/",
        corporation_ledger.corporation_ledger,
        name="corporation_ledger",
    ),
    path(
        "corporation/<int:corporation_id>/division/<int:division_id>/date/<int:year>/",
        corporation_ledger.corporation_ledger,
        name="corporation_ledger",
    ),
    path(
        "corporation/<int:corporation_id>/division/<int:division_id>/date/<int:year>/<int:month>/",
        corporation_ledger.corporation_ledger,
        name="corporation_ledger",
    ),
    path(
        "corporation/<int:corporation_id>/division/<int:division_id>/date/<int:year>/<int:month>/<int:day>/",
        corporation_ledger.corporation_ledger,
        name="corporation_ledger",
    ),
    # -- -- Data Export
    path(
        "corporation/<int:corporation_id>/data-export/",
        corporation_ledger.corporation_data_export,
        name="corporation_data_export",
    ),
    path(
        "corporation/<int:corporation_id>/data-export/generate/",
        corporation_ledger.corporation_data_export_generate,
        name="corporation_data_export_generate",
    ),
    path(
        "corporation/<str:hash_code>/data-export/download/",
        corporation_ledger.corporation_download_export_file,
        name="corporation_download_export_file",
    ),
    path(
        "corporation/<str:hash_code>/data-export/update/",
        corporation_ledger.corporation_data_export_run_update,
        name="corporation_data_export_run_update",
    ),
    # -- -- Corporation Details
    path(
        "corporation/<int:corporation_id>/view/details/<int:entity_id>/section/<str:section>/",
        corporation_ledger.corporation_details,
        name="corporation_details",
    ),
    path(
        "corporation/<int:corporation_id>/<int:year>/view/details/<int:entity_id>/section/<str:section>/",
        corporation_ledger.corporation_details,
        name="corporation_details",
    ),
    path(
        "corporation/<int:corporation_id>/<int:year>/<int:month>/view/details/<int:entity_id>/section/<str:section>/",
        corporation_ledger.corporation_details,
        name="corporation_details",
    ),
    path(
        "corporation/<int:corporation_id>/<int:year>/<int:month>/<int:day>/view/details/<int:entity_id>/section/<str:section>/",
        corporation_ledger.corporation_details,
        name="corporation_details",
    ),
    # -- -- Division Details
    path(
        "corporation/<int:corporation_id>/division/<int:division_id>/view/details/<int:entity_id>/section/<str:section>/",
        corporation_ledger.corporation_details,
        name="corporation_details",
    ),
    path(
        "corporation/<int:corporation_id>/division/<int:division_id>/<int:year>/view/details/<int:entity_id>/section/<str:section>/",
        corporation_ledger.corporation_details,
        name="corporation_details",
    ),
    path(
        "corporation/<int:corporation_id>/division/<int:division_id>/<int:year>/<int:month>/view/details/<int:entity_id>/section/<str:section>/",
        corporation_ledger.corporation_details,
        name="corporation_details",
    ),
    path(
        "corporation/<int:corporation_id>/division/<int:division_id>/<int:year>/<int:month>/<int:day>/view/details/<int:entity_id>/section/<str:section>/",
        corporation_ledger.corporation_details,
        name="corporation_details",
    ),
    path(
        "corporation/<int:corporation_id>/division/<int:division_id>/view/details/<int:entity_id>/section/<str:section>/",
        corporation_ledger.corporation_details,
        name="corporation_details",
    ),
    path(
        "corporation/<int:corporation_id>/view/administration/",
        corporation_ledger.corporation_administration,
        name="corporation_administration",
    ),
    path(
        "corporation/view/overview/",
        corporation_ledger.corporation_overview,
        name="corporation_overview",
    ),
    # -- -- Character Ledger
    path(
        "character/<int:character_id>/",
        character_ledger.character_ledger,
        name="character_ledger",
    ),
    path(
        "character/<int:character_id>/date/<int:year>/",
        character_ledger.character_ledger,
        name="character_ledger",
    ),
    path(
        "character/<int:character_id>/date/<int:year>/<int:month>/",
        character_ledger.character_ledger,
        name="character_ledger",
    ),
    path(
        "character/<int:character_id>/date/<int:year>/<int:month>/<int:day>/",
        character_ledger.character_ledger,
        name="character_ledger",
    ),
    path(
        "character/<int:character_id>/section/<str:section>/",
        character_ledger.character_ledger,
        name="character_ledger",
    ),
    path(
        "character/<int:character_id>/date/<int:year>/section/<str:section>/",
        character_ledger.character_ledger,
        name="character_ledger",
    ),
    path(
        "character/<int:character_id>/date/<int:year>/<int:month>/section/<str:section>/",
        character_ledger.character_ledger,
        name="character_ledger",
    ),
    path(
        "character/<int:character_id>/date/<int:year>/<int:month>/<int:day>/section/<str:section>/",
        character_ledger.character_ledger,
        name="character_ledger",
    ),
    # -- -- Character Details
    path(
        "character/<int:character_id>/view/details/section/<str:section>/",
        character_ledger.character_details,
        name="character_details",
    ),
    path(
        "character/<int:character_id>/<int:year>/view/details/section/<str:section>/",
        character_ledger.character_details,
        name="character_details",
    ),
    path(
        "character/<int:character_id>/<int:year>/<int:month>/view/details/section/<str:section>/",
        character_ledger.character_details,
        name="character_details",
    ),
    path(
        "character/<int:character_id>/<int:year>/<int:month>/<int:day>/view/details/section/<str:section>/",
        character_ledger.character_details,
        name="character_details",
    ),
    path(
        "character/<int:character_id>/<int:year>/<int:month>/<int:day>/view/details/section/<str:section>/",
        character_ledger.character_details,
        name="character_details",
    ),
    # -- -- Character Administration
    path(
        "character/<int:character_id>/view/administration/",
        character_ledger.character_administration,
        name="character_administration",
    ),
    path(
        "character/view/overview/",
        character_ledger.character_overview,
        name="character_overview",
    ),
    # -- -- Planetary
    path(
        "character/view/planetary/",
        planetary.planetary_ledger_index,
        name="planetary_ledger_index",
    ),
    path(
        "character/<int:character_id>/view/planetary/",
        planetary.planetary_ledger,
        name="planetary_ledger",
    ),
    path(
        "character/switch_alarm/",
        planetary.switch_alarm,
        name="switch_alarm",
    ),
    path(
        "character/view/planetary/overview/",
        planetary.planetary_overview,
        name="planetary_overview",
    ),
    # -- API System
    re_path(r"^api/", api.urls),
]
