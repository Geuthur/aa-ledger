"""App Tasks"""

import logging

from celery import chain, shared_task

from django.db.models import DateTimeField
from django.db.models.functions import Least
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.notifications import notify
from allianceauth.services.tasks import QueueOnce

from ledger import app_settings
from ledger.decorators import when_esi_is_available
from ledger.models.characteraudit import CharacterAudit
from ledger.models.corporationaudit import CorporationAudit
from ledger.models.planetary import CharacterPlanetDetails
from ledger.task_helpers.char_helpers import (
    update_character_mining,
    update_character_wallet,
)
from ledger.task_helpers.corp_helpers import update_corp_wallet_division
from ledger.task_helpers.plan_helpers import (
    update_character_planetary,
    update_character_planetary_details,
)

logger = logging.getLogger(__name__)

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
    **{"once": {"keys": ["character_id"], "graceful": True}},
}

_update_ledger_corp_params = {
    **TASK_DEFAULTS_ONCE,
    **{"once": {"keys": ["corporation_id"], "graceful": True}},
}


@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_all_characters(runs: int = 0):
    """Update all characters"""
    characters = CharacterAudit.objects.select_related("character").all()
    for char in characters:
        update_character.apply_async(args=[char.character.character_id])
        runs = runs + 1
    logger.debug("Queued %s Character Audit Tasks", runs)


@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_subset_characters(subset=5, min_runs=10, max_runs=200, force_refresh=False):
    """Update a batch of characters to prevent overload ESI"""
    total_characters = CharacterAudit.objects.filter(active=1).count()
    characters_count = min(max(total_characters // subset, min_runs), total_characters)

    # Limit the number of characters to update to prevent overload ESI
    characters_count = min(characters_count, max_runs)

    # Annotate characters with the oldest update timestamp and order by it
    characters = (
        CharacterAudit.objects.filter(active=1)
        .annotate(
            oldest_update=Least(
                "last_update_wallet",
                "last_update_mining",
                "last_update_planetary",
                output_field=DateTimeField(),
            )
        )
        .order_by("oldest_update")[:characters_count]
    )

    for char in characters:
        update_character.apply_async(
            args=[char.character.character_id], force_refresh=force_refresh
        )
    logger.debug("Queued %s Character Audit Tasks", len(characters))


@shared_task(**_update_ledger_char_params)
@when_esi_is_available
def update_character(character_id: int, force_refresh=False):
    character = CharacterAudit.objects.get(character__character_id=character_id)

    # Settings for Task Queue
    skip_date = timezone.now() - timezone.timedelta(
        minutes=app_settings.LEDGER_STALE_STATUS
    )
    que = []
    mindt = timezone.now() - timezone.timedelta(days=7)
    priority = 7

    logger.debug(
        "Processing Audit Updates for %s", format(character.character.character_name)
    )

    if (character.last_update_mining or mindt) <= skip_date or force_refresh:
        que.append(
            update_char_mining_ledger.si(
                character.character.character_id, force_refresh=force_refresh
            ).set(priority=priority)
        )

    if (character.last_update_wallet or mindt) <= skip_date or force_refresh:
        que.append(
            update_char_wallet.si(
                character.character.character_id, force_refresh=force_refresh
            ).set(priority=priority)
        )

    if (character.last_update_planetary or mindt) <= skip_date or force_refresh:
        que.append(
            update_char_planets.si(
                character.character.character_id, force_refresh=force_refresh
            ).set(priority=priority)
        )

    chain(que).apply_async()
    logger.info(
        "Queued %s Audit Updates for %s",
        len(que),
        character.character.character_name,
    )


@shared_task(**_update_ledger_char_params)
def update_char_mining_ledger(character_id, force_refresh=False):
    return update_character_mining(character_id, force_refresh=force_refresh)


@shared_task(**_update_ledger_char_params)
def update_char_wallet(
    character_id, force_refresh=False
):  # pylint: disable=unused-argument, dangerous-default-value
    return update_character_wallet(character_id, force_refresh=force_refresh)


@shared_task(**_update_ledger_char_params)
def update_char_planets(
    character_id, force_refresh=False
):  # pylint: disable=unused-argument, dangerous-default-value
    return update_character_planetary(character_id, force_refresh=force_refresh)


@shared_task(**_update_ledger_char_params)
def update_char_planets_details(
    character_id, planet_id, force_refresh=False
):  # pylint: disable=unused-argument, dangerous-default-value
    return update_character_planetary_details(
        character_id, planet_id, force_refresh=force_refresh
    )


# pylint: disable=unused-argument, too-many-locals
@shared_task(**TASK_DEFAULTS_ONCE)
def check_planetary_alarms(runs: int = 0):
    all_planets = CharacterPlanetDetails.objects.all()
    owner_ids = {}
    warnings = {}

    for planet in all_planets:
        if planet.is_expired and not planet.notification_sent and planet.notification:
            character_id = planet.planet.character.character.character_id

            # Determine if the character_id is part of any main character's alts
            main_id = None
            for main, alts in owner_ids.items():
                if character_id in alts:
                    main_id = main
                    break

            if main_id is None:
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
                "charname": planet.planet.character.character.character_name,
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

                full_message = format_html(
                    "Following Planet Extractor Heads have expired: \n{}", msg
                )
                notify(
                    title=title,
                    message=full_message,
                    user=owner.user,
                    level="warning",
                )
                runs = runs + 1
    logger.info("Queued %s Planetary Alarms.", runs)


# Corporation Audit - Tasks
@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_all_corps(runs: int = 0):
    corps = CorporationAudit.objects.select_related("corporation").all()
    for corp in corps:
        update_corp.apply_async(args=[corp.corporation.corporation_id])
        runs = runs + 1
    logger.debug("Queued %s Corporation Audit Tasks", runs)


@shared_task(**_update_ledger_corp_params)
@when_esi_is_available
def update_corp(corporation_id, force_refresh=False):  # pylint: disable=unused-argument
    corp = CorporationAudit.objects.get(corporation__corporation_id=corporation_id)
    logger.debug("Processing Audit Updates for %s", corp.corporation.corporation_name)

    # Settings for Task Queue
    skip_date = timezone.now() - timezone.timedelta(
        minutes=app_settings.LEDGER_STALE_STATUS
    )
    mindt = timezone.now() - timezone.timedelta(days=7)
    priority = 7

    if (corp.last_update_wallet or mindt) <= skip_date or force_refresh:
        update_corp_wallet.si(corporation_id, force_refresh=force_refresh).set(
            priority=priority
        ).apply_async()

    logger.info("Queued Audit Updates for %s", corp.corporation.corporation_name)


@shared_task(**_update_ledger_corp_params)
def update_corp_wallet(corporation_id, force_refresh=False):
    return update_corp_wallet_division(corporation_id, force_refresh=force_refresh)
