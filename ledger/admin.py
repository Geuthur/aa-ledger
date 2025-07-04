"""Admin models"""

# Django
from django.contrib import admin
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db.models import Max, Q
from django.utils import timezone
from django.utils.html import format_html
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.evelinks import eveimageserver

# AA Ledger
from ledger.models.characteraudit import CharacterAudit, CharacterUpdateStatus
from ledger.models.corporationaudit import CorporationAudit, CorporationUpdateStatus


class CorporationUpdateStatusAdminInline(admin.TabularInline):
    model = CorporationUpdateStatus
    fields = (
        "section",
        "_is_enabled",
        "_is_success",
        "_is_token_ok",
        "error_message",
        "run_finished_at",
        "_run_duration",
        "update_finished_at",
        "_update_duration",
    )
    readonly_fields = (
        "_is_enabled",
        "_is_success",
        "_is_token_ok",
        "_run_duration",
        "_update_duration",
    )
    ordering = ["section"]

    # pylint: disable=unused-argument
    def has_add_permission(self, request, obj=None):
        return False

    # pylint: disable=unused-argument
    def has_change_permission(self, request, obj=None):
        return False

    # pylint: disable=unused-argument
    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(boolean=True)
    def _is_enabled(self, obj: CorporationUpdateStatus) -> bool:
        return obj.is_enabled

    @admin.display(boolean=True)
    def _is_success(self, obj: CorporationUpdateStatus) -> bool:
        if not obj.is_enabled:
            return None
        return obj.is_success

    @admin.display(boolean=True)
    def _is_token_ok(self, obj: CorporationUpdateStatus) -> bool:
        return not obj.has_token_error

    @admin.display
    def _run_duration(self, obj: CorporationUpdateStatus) -> float:
        return self._calc_duration(obj.last_run_at, obj.last_run_finished_at)

    @admin.display
    def _update_duration(self, obj: CorporationUpdateStatus) -> float:
        return self._calc_duration(obj.last_update_at, obj.last_update_finished_at)

    @staticmethod
    def _calc_duration(
        started_at: timezone.datetime, finished_at: timezone.datetime
    ) -> timezone.timedelta:
        if not started_at or not finished_at:
            return "-"

        return timesince(finished_at - started_at)


@admin.register(CorporationAudit)
class CorporationAuditAdmin(admin.ModelAdmin):
    list_display = (
        "_entity_pic",
        "_corporation__corporation_id",
        "_last_update_at",
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

    inlines = (CorporationUpdateStatusAdminInline,)

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.prefetch_related("ledger_corporation_update_status").annotate(
            last_update_at=Max(
                "ledger_corporation_update_status__last_run_finished_at",
                filter=~Q(ledger_corporation_update_status__section="wallet_journal"),
            )
        )

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

    @admin.display(ordering="last_update_at", description=_("last update run"))
    def _last_update_at(self, obj: CorporationAudit):
        return naturaltime(obj.last_update_at) if obj.last_update_at else "-"

    # pylint: disable=unused-argument
    def has_add_permission(self, request):
        return False

    # pylint: disable=unused-argument
    def has_change_permission(self, request, obj=None):
        return False


class CharacterUpdateStatusAdminInline(admin.TabularInline):
    model = CharacterUpdateStatus
    fields = (
        "section",
        "_is_enabled",
        "_is_success",
        "_is_token_ok",
        "error_message",
        "run_finished_at",
        "_run_duration",
        "update_finished_at",
        "_update_duration",
    )
    readonly_fields = (
        "_is_enabled",
        "_is_success",
        "_is_token_ok",
        "_run_duration",
        "_update_duration",
    )
    ordering = ["section"]

    # pylint: disable=unused-argument
    def has_add_permission(self, request, obj=None):
        return False

    # pylint: disable=unused-argument
    def has_change_permission(self, request, obj=None):
        return False

    # pylint: disable=unused-argument
    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(boolean=True)
    def _is_enabled(self, obj: CharacterUpdateStatus) -> bool:
        return obj.is_enabled

    @admin.display(boolean=True)
    def _is_success(self, obj: CharacterUpdateStatus) -> bool:
        if not obj.is_enabled:
            return None
        return obj.is_success

    @admin.display(boolean=True)
    def _is_token_ok(self, obj: CharacterUpdateStatus) -> bool:
        return not obj.has_token_error

    @admin.display
    def _run_duration(self, obj: CharacterUpdateStatus) -> float:
        return self._calc_duration(obj.last_run_at, obj.last_run_finished_at)

    @admin.display
    def _update_duration(self, obj: CharacterUpdateStatus) -> float:
        return self._calc_duration(obj.last_update_at, obj.last_update_finished_at)

    @staticmethod
    def _calc_duration(
        started_at: timezone.datetime, finished_at: timezone.datetime
    ) -> str:
        if not started_at or not finished_at:
            return "-"
        return timesince(finished_at - started_at)


@admin.register(CharacterAudit)
class CharacterAuditAdmin(admin.ModelAdmin):
    list_display = (
        "_entity_pic",
        "_character__character_name",
        "_last_update_at",
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

    inlines = (CharacterUpdateStatusAdminInline,)

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.prefetch_related("ledger_update_status").annotate(
            last_update_at=Max(
                "ledger_update_status__last_run_finished_at",
                filter=~Q(ledger_update_status__section="wallet_journal"),
            )
        )

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

    @admin.display(ordering="last_update_at", description=_("last update run"))
    def _last_update_at(self, obj: CharacterAudit):
        return naturaltime(obj.last_update_at) if obj.last_update_at else "-"

    # pylint: disable=unused-argument
    def has_add_permission(self, request):
        return False

    # pylint: disable=unused-argument
    def has_change_permission(self, request, obj=None):
        return False
