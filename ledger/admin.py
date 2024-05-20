"""Admin models"""

from django.contrib import admin
from django.utils.html import format_html

from allianceauth.eveonline.evelinks import eveimageserver

from ledger.models.characteraudit import CharacterAudit
from ledger.models.corporationaudit import CorporationAudit


@admin.register(CorporationAudit)
class CorporationAuditAdmin(admin.ModelAdmin):
    list_display = (
        "_entity_pic",
        "_corporation__corporation_id",
        "_last_update_wallet",
    )

    list_display_links = (
        "_entity_pic",
        "_corporation__corporation_id",
    )

    list_select_related = ("corporation",)

    ordering = ["corporation__corporation_name"]

    search_fields = ["corporation__corporation_name", "corporation__corporation_id"]

    actions = [
        "delete_objects",
    ]

    @admin.display(description="")
    def _entity_pic(self, obj: CorporationAudit):
        eve_id = obj.corporation.corporation_id
        return format_html(
            '<img src="{}" class="img-circle">',
            eveimageserver._eve_entity_image_url("corporation", eve_id, 32),
        )

    @admin.display(description="Corporation ID", ordering="corporation__corporation_id")
    def _corporation__corporation_id(self, obj: CorporationAudit):
        return obj.corporation.corporation_id

    @admin.display(description="Last Update Wallet", ordering="last_update_wallet")
    def _last_update_wallet(self, obj: CorporationAudit):
        return obj.last_update_wallet

    # pylint: disable=unused-argument
    def has_add_permission(self, request):
        return False

    # pylint: disable=unused-argument
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CharacterAudit)
class CharacterAuditAdmin(admin.ModelAdmin):
    list_display = (
        "_entity_pic",
        "_character__character_name",
        "_last_update_wallet",
        "_last_update_mining",
    )

    list_display_links = (
        "_entity_pic",
        "_character__character_name",
    )

    list_select_related = ("character",)

    ordering = ["character__character_name"]

    search_fields = ["character__character_name"]

    actions = [
        "delete_objects",
    ]

    @admin.display(description="")
    def _entity_pic(self, obj: CharacterAudit):
        eve_id = obj.character.character_id
        return format_html(
            '<img src="{}" class="img-circle">',
            eveimageserver._eve_entity_image_url("character", eve_id, 32),
        )

    @admin.display(description="Character Name", ordering="character__character_name")
    def _character__character_name(self, obj: CharacterAudit):
        return obj.character.character_name

    @admin.display(description="Last Update Wallet", ordering="last_update_wallet")
    def _last_update_wallet(self, obj: CharacterAudit):
        return obj.last_update_wallet

    @admin.display(description="Last Update Mining", ordering="last_update_mining")
    def _last_update_mining(self, obj: CharacterAudit):
        return obj.last_update_mining

    # pylint: disable=unused-argument
    def has_add_permission(self, request):
        return False

    # pylint: disable=unused-argument
    def has_change_permission(self, request, obj=None):
        return False
