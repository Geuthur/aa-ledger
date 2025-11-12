"""App Tasks"""

# Standard Library
import inspect
from collections.abc import Callable

# Third Party
from celery import chain, shared_task

# Django
from django.db.models import Min
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership, User
from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__, app_settings
from ledger.decorators import when_esi_is_available
from ledger.helpers import data_exporter
from ledger.helpers.discord import send_user_notification
from ledger.models.characteraudit import CharacterAudit
from ledger.models.corporationaudit import CorporationAudit
from ledger.models.planetary import CharacterPlanetDetails

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

MAX_RETRIES_DEFAULT = 3

# Default params for all tasks.
TASK_DEFAULTS = {
    "time_limit": app_settings.LEDGER_TASKS_TIME_LIMIT,
    "max_retries": MAX_RETRIES_DEFAULT,
}

# Default params for tasks that need run once only.
TASK_DEFAULTS_ONCE = {**TASK_DEFAULTS, **{"base": QueueOnce}}

_update_ledger_char_params = {
    **TASK_DEFAULTS_ONCE,
    **{"once": {"keys": ["character_pk", "force_refresh"], "graceful": True}},
}

_update_ledger_corp_params = {
    **TASK_DEFAULTS_ONCE,
    **{"once": {"keys": ["corporation_pk", "force_refresh"], "graceful": True}},
}


# pylint: disable=unused-argument, too-many-locals
@shared_task(**TASK_DEFAULTS_ONCE)
def check_planetary_alarms(runs: int = 0):
    all_planets = CharacterPlanetDetails.objects.all()
    owner_ids = {}
    warnings = {}

    for planet in all_planets:
        if planet.is_expired and not planet.notification_sent and planet.notification:
            character_id = planet.planet.character.eve_character.character_id

            try:
                owner = CharacterOwnership.objects.get(
                    character__character_id=character_id
                )
                main = owner.user.profile.main_character
                alts = main.character_ownership.user.character_ownerships.all()

                owner_ids[main.character_id] = alts.values_list(
                    "character__character_id", flat=True
                )

                main_id = main.character_id
            except CharacterOwnership.DoesNotExist:
                continue
            except AttributeError:
                continue

            msg = _("%(charname)s on %(planetname)s") % {
                "charname": planet.planet.character.eve_character.character_name,
                "planetname": planet.planet.planet.name,
            }

            if main_id not in warnings:
                warnings[main_id] = []

            warnings[main_id].append(msg)
            planet.notification_sent = True
            planet.save()

    if warnings:
        for main_id, messages in warnings.items():
            owner = CharacterOwnership.objects.get(character__character_id=main_id)
            title = _("Planetary Extractor Heads Expired")

            # Split messages into chunks of 50
            for i in range(0, len(messages), 50):
                chunk = messages[i : i + 50]
                msg = "\n".join(chunk)

                full_message = format_html(msg)

                send_user_notification.delay(
                    user_id=owner.user.id,
                    title=title,
                    message=full_message,
                    embed_message=True,
                    level="warning",
                )
                runs = runs + 1
    logger.info("Queued %s Planetary Alarms.", runs)


@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_all_characters(runs: int = 0, force_refresh=False):
    """Update all characters"""
    # Disable characters with no owner
    CharacterAudit.objects.disable_characters_with_no_owner()
    characters = CharacterAudit.objects.select_related("eve_character").filter(active=1)
    for char in characters:
        update_character.apply_async(
            args=[char.pk], kwargs={"force_refresh": force_refresh}
        )
        runs = runs + 1
    logger.debug("Queued %s Character Audit Tasks", runs)


@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_subset_characters(subset=2, min_runs=50, max_runs=500, force_refresh=False):
    """Update a batch of characters to prevent overload ESI"""
    # Disable characters with no owner
    CharacterAudit.objects.disable_characters_with_no_owner()
    total_characters = CharacterAudit.objects.filter(active=1).count()
    characters_count = min(max(total_characters // subset, min_runs), total_characters)

    # Limit the number of characters to update to prevent overload ESI
    characters_count = min(characters_count, max_runs)

    # Annotate characters with the oldest `last_run_finished` across all update sections
    characters = (
        CharacterAudit.objects.filter(active=1)
        .annotate(oldest_update=Min("ledger_update_status__last_run_finished_at"))
        .order_by("oldest_update")
        .distinct()[:characters_count]
    )

    for char in characters:
        update_character.apply_async(
            args=[char.pk], kwargs={"force_refresh": force_refresh}
        )
    logger.debug("Queued %s Character Audit Tasks", len(characters))


@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_character(character_pk: int, force_refresh=False):
    character = CharacterAudit.objects.prefetch_related("ledger_update_status").get(
        pk=character_pk
    )

    que = []
    priority = 7

    logger.debug(
        "Processing Audit Updates for %s",
        format(character.eve_character.character_name),
    )

    if force_refresh:
        # Reset Token Error if we are forcing a refresh
        character.reset_has_token_error()

    needs_update = character.calc_update_needed()

    if not needs_update and not force_refresh:
        logger.info("No updates needed for %s", character.eve_character.character_name)
        return

    sections = character.UpdateSection.get_sections()

    for section in sections:
        # Skip sections that are not in the needs_update list
        if not force_refresh and not needs_update.for_section(section):
            logger.debug(
                "No updates needed for %s (%s)",
                character.eve_character.character_name,
                section,
            )
            continue

        task_name = f"update_char_{section}"
        task = globals().get(task_name)
        que.append(
            task.si(character.pk, force_refresh=force_refresh).set(priority=priority)
        )

    chain(que).apply_async()
    logger.debug(
        "Queued %s Audit Updates for %s",
        len(que),
        character.eve_character.character_name,
    )


@shared_task(**_update_ledger_char_params)
@when_esi_is_available
def update_char_wallet_journal(character_pk: int, force_refresh: bool):
    return _update_character_section(
        character_pk,
        section=CharacterAudit.UpdateSection.WALLET_JOURNAL,
        force_refresh=force_refresh,
    )


@shared_task(**_update_ledger_char_params)
@when_esi_is_available
def update_char_mining_ledger(character_pk: int, force_refresh: bool):
    return _update_character_section(
        character_pk,
        section=CharacterAudit.UpdateSection.MINING_LEDGER,
        force_refresh=force_refresh,
    )


@shared_task(**_update_ledger_char_params)
@when_esi_is_available
def update_char_planets(character_pk: int, force_refresh: bool):
    logger.debug("Updating Planet Data for %s", character_pk)
    return _update_character_section(
        character_pk,
        section=CharacterAudit.UpdateSection.PLANETS,
        force_refresh=force_refresh,
    )


@shared_task(**_update_ledger_char_params)
@when_esi_is_available
def update_char_planets_details(character_pk: int, force_refresh: bool):
    logger.debug("Updating Planet Details for %s", character_pk)
    return _update_character_section(
        character_pk,
        section=CharacterAudit.UpdateSection.PLANETS_DETAILS,
        force_refresh=force_refresh,
    )


def _update_character_section(character_pk: int, section: str, force_refresh: bool):
    """Update a specific section of the character audit."""
    section = CharacterAudit.UpdateSection(section)
    character = CharacterAudit.objects.get(pk=character_pk)
    logger.debug(
        "Updating %s for %s", section.label, character.eve_character.character_name
    )

    character.reset_update_status(section)

    method: Callable = getattr(character, section.method_name)
    method_signature = inspect.signature(method)

    if "force_refresh" in method_signature.parameters:
        kwargs = {"force_refresh": force_refresh}
    else:
        kwargs = {}
    result = character.perform_update_status(section, method, **kwargs)
    character.update_section_log(section, result)


# Corporation Audit - Tasks
@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_all_corporations(runs: int = 0, force_refresh=False):
    corps = CorporationAudit.objects.select_related("corporation").filter(active=1)
    for corp in corps:
        update_corporation.apply_async(
            args=[corp.pk], kwargs={"force_refresh": force_refresh}
        )
        runs = runs + 1
    logger.info("Queued %s Corporation Audit Tasks", runs)


@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_subset_corporations(
    subset=5, min_runs=20, max_runs=200, force_refresh=False
):
    """Update a batch of corporations to prevent overload ESI"""
    total_corporations = CorporationAudit.objects.filter(active=1).count()
    corporations_count = min(
        max(total_corporations // subset, min_runs), total_corporations
    )

    # Limit the number of corporations to update to prevent overload ESI
    corporations_count = min(corporations_count, max_runs)

    # Annotate corporations with the oldest `last_run_finished` across all update sections
    corporations = (
        CorporationAudit.objects.filter(active=1)
        .annotate(
            oldest_update=Min("ledger_corporation_update_status__last_run_finished_at")
        )
        .order_by("oldest_update")
        .distinct()[:corporations_count]
    )

    for corp in corporations:
        update_corporation.apply_async(
            args=[corp.pk], kwargs={"force_refresh": force_refresh}
        )
    logger.debug("Queued %s Corporation Audit Tasks", len(corporations))


@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_corporation(
    corporation_pk, force_refresh=False
):  # pylint: disable=unused-argument
    corporation = CorporationAudit.objects.prefetch_related(
        "ledger_corporation_update_status"
    ).get(pk=corporation_pk)

    que = []
    priority = 7

    logger.debug(
        "Processing Audit Updates for %s",
        format(corporation.corporation.corporation_name),
    )

    if force_refresh:
        # Reset Token Error if we are forcing a refresh
        corporation.reset_has_token_error()

    needs_update = corporation.calc_update_needed()

    if not needs_update and not force_refresh:
        logger.info(
            "No updates needed for %s", corporation.corporation.corporation_name
        )
        return

    sections = corporation.UpdateSection.get_sections()

    for section in sections:
        # Skip sections that are not in the needs_update list
        if not force_refresh and not needs_update.for_section(section):
            logger.debug(
                "No updates needed for %s (%s)",
                corporation.corporation.corporation_name,
                section,
            )
            continue

        task_name = f"update_corp_{section}"
        task = globals().get(task_name)
        que.append(
            task.si(corporation.pk, force_refresh=force_refresh).set(priority=priority)
        )

    chain(que).apply_async()
    logger.debug(
        "Queued %s Audit Updates for %s",
        len(que),
        corporation.corporation.corporation_name,
    )


@shared_task(**_update_ledger_corp_params)
@when_esi_is_available
def update_corp_wallet_division_names(corporation_pk: int, force_refresh: bool):
    return _update_corporation_section(
        corporation_pk,
        section=CorporationAudit.UpdateSection.WALLET_DIVISION_NAMES,
        force_refresh=force_refresh,
    )


@shared_task(**_update_ledger_corp_params)
@when_esi_is_available
def update_corp_wallet_division(corporation_pk: int, force_refresh: bool):
    return _update_corporation_section(
        corporation_pk,
        section=CorporationAudit.UpdateSection.WALLET_DIVISION,
        force_refresh=force_refresh,
    )


@shared_task(**_update_ledger_corp_params)
@when_esi_is_available
def update_corp_wallet_journal(corporation_pk: int, force_refresh: bool):
    return _update_corporation_section(
        corporation_pk,
        section=CorporationAudit.UpdateSection.WALLET_JOURNAL,
        force_refresh=force_refresh,
    )


def _update_corporation_section(corporation_pk: int, section: str, force_refresh: bool):
    """Update a specific section of the character audit."""
    section = CorporationAudit.UpdateSection(section)
    corporation = CorporationAudit.objects.get(pk=corporation_pk)
    logger.debug(
        "Updating %s for %s", section.label, corporation.corporation.corporation_name
    )

    corporation.reset_update_status(section)

    method: Callable = getattr(corporation, section.method_name)
    method_signature = inspect.signature(method)

    if "force_refresh" in method_signature.parameters:
        kwargs = {"force_refresh": force_refresh}
    else:
        kwargs = {}

    result = corporation.perform_update_status(section, method, **kwargs)
    corporation.update_section_log(section, result)


@shared_task(**TASK_DEFAULTS_ONCE)
def clear_all_etags():
    logger.debug("Clearing all etags")
    try:
        # Third Party
        # pylint: disable=import-outside-toplevel
        from django_redis import get_redis_connection

        _client = get_redis_connection("default")
    except (NotImplementedError, ModuleNotFoundError):
        # Django
        # pylint: disable=import-outside-toplevel
        from django.core.cache import caches

        default_cache = caches["default"]
        _client = default_cache.get_master_client()
    keys = _client.keys(f":?:{app_settings.LEDGER_CACHE_KEY}-*")
    logger.info("Deleting %s etag keys", len(keys))
    if keys:
        deleted = _client.delete(*keys)
        logger.info("Deleted %s etag keys", deleted)
    else:
        logger.info("No etag keys to delete")


@shared_task(**TASK_DEFAULTS_ONCE)
# pylint: disable=too-many-positional-arguments
def export_data_ledger(
    user_pk: int,
    ledger_type: str,
    entity_id: int,
    division_id: int = None,
    year: int = None,
    month: int = None,
):
    """Export data for a ledger."""
    msg = data_exporter.export_ledger_to_archive(
        ledger_type, entity_id, division_id, year, month
    )

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.debug("User with pk %s does not exist", user_pk)
        return

    if not msg:
        title = _(f"{ledger_type.capitalize()} Data Export Ready")
        message = _(
            f"Your data export for topic {ledger_type} is ready. You can download it from the Data Export page.",
        )
    else:
        title = _(f"{ledger_type.capitalize()} Data Export Failed")
        message = _(
            f"Your data export for topic {ledger_type} has failed with following error: {msg}",
        )

    send_user_notification.delay(
        user_id=user.pk,
        title=title,
        message=message,
        embed_message=True,
        level="info",
    )
