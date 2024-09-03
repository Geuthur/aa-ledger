"""App Tasks"""

# Standard Library
import datetime

# Third Party
# pylint: disable=no-name-in-module
from celery import shared_task

from django.db import IntegrityError
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from esi.errors import TokenExpiredError
from esi.models import Token

from allianceauth.authentication.models import CharacterOwnership, EveCharacter
from allianceauth.notifications import notify
from allianceauth.services.tasks import QueueOnce

from ledger.decorators import when_esi_is_available
from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import CharacterAudit
from ledger.models.corporationaudit import CorporationAudit
from ledger.models.planetary import CharacterPlanetDetails
from ledger.task_helpers.char_helpers import (
    update_character_mining,
    update_character_wallet,
)
from ledger.task_helpers.core_helpers import enqueue_next_task, no_fail_chain
from ledger.task_helpers.corp_helpers import update_corp_wallet_division
from ledger.task_helpers.plan_helpers import (
    update_character_planetary,
    update_character_planetary_details,
)

logger = get_extension_logger(__name__)


# Member Audit Adaptation
# pylint: disable=unused-argument
@shared_task(bind=True, base=QueueOnce)
@when_esi_is_available
def create_member_audit(self, runs: int = 0):
    # pylint: disable=import-outside-toplevel
    from memberaudit.models import Character

    chars_ids = CharacterAudit.objects.all().values_list(
        "character__character_id", flat=True
    )
    member_ids = Character.objects.all().values_list(
        "eve_character__character_id", flat=True
    )

    new_ids = set(member_ids) - set(chars_ids)

    for character_id in new_ids:
        try:
            CharacterAudit.objects.update_or_create(
                character=EveCharacter.objects.get_character_by_id(character_id)
            )
            runs = runs + 1
        except IntegrityError:
            continue
    logger.debug("Created %s missing Member Audit Characters", runs)
    return True


# Character Audit - Tasks
# pylint: disable=unused-argument
@shared_task(bind=True, base=QueueOnce)
@when_esi_is_available
def create_missing_character(self, chars_list: list, runs: int = 0):
    for character_id in chars_list:
        try:
            EveCharacter.objects.create_character(
                character_id=character_id,
            )
            runs = runs + 1
        except IntegrityError:
            continue
    logger.info("Created %s missing Characters", runs)
    return True


@shared_task
@when_esi_is_available
def update_all_characters(runs: int = 0):
    characters = CharacterAudit.objects.select_related("character").all()
    for char in characters:
        update_character.apply_async(args=[char.character.character_id])
        runs = runs + 1
    logger.info("Queued %s Char Audit Updates", runs)


@shared_task(bind=True, base=QueueOnce)
def update_character(
    self, char_id, force_refresh=False
):  # pylint: disable=unused-argument
    character = (
        CharacterAudit.objects.select_related("character")
        .filter(character__character_id=char_id)
        .first()
    )
    if character is None:
        token = Token.get_token(char_id, CharacterAudit.get_esi_scopes())
        if token:
            try:
                if token.valid_access_token():
                    character, _ = CharacterAudit.objects.update_or_create(
                        character=EveCharacter.objects.get_character_by_id(
                            token.character_id
                        )
                    )
                else:
                    return False
            except TokenExpiredError:
                return False
        else:
            logger.info("No Tokens for %s", char_id)
            return False

    logger.debug(
        "Processing Audit Updates for %s", format(character.character.character_name)
    )

    skip_date = timezone.now() - datetime.timedelta(hours=1)
    que = []
    mindt = timezone.now() - datetime.timedelta(days=90)

    if (character.last_update_mining or mindt) <= skip_date or force_refresh:
        que.append(
            update_char_mining_ledger.si(
                character.character.character_id, force_refresh=force_refresh
            )
        )

    if (character.last_update_wallet or mindt) <= skip_date or force_refresh:
        que.append(
            update_char_wallet.si(
                character.character.character_id, force_refresh=force_refresh
            )
        )

    if (character.last_update_planetary or mindt) <= skip_date or force_refresh:
        que.append(
            update_char_planets.si(
                character.character.character_id, force_refresh=force_refresh
            )
        )

    enqueue_next_task(que)

    logger.debug(
        "Queued %s Audit Updates for %s",
        len(que) + 1,
        character.character.character_name,
    )

    return True


# pylint: disable=unused-argument, too-many-locals
@shared_task(bind=True, base=QueueOnce)
def check_planetary_alarms(self, runs: int = 0):
    all_planets = CharacterPlanetDetails.objects.all()
    owner_ids = {}
    warnings = {}

    for planet in all_planets:
        if planet.is_expired() and not planet.notification_sent and planet.notification:
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


@shared_task
@when_esi_is_available
def update_all_corps(runs: int = 0):
    corps = CorporationAudit.objects.select_related("corporation").all()
    for corp in corps:
        update_corp.apply_async(args=[corp.corporation.corporation_id])
        runs = runs + 1
    logger.info("Queued %s Corp Audit Updates", runs)


@shared_task(bind=True, base=QueueOnce)
def update_corp(self, corp_id, force_refresh=False):  # pylint: disable=unused-argument
    corp = CorporationAudit.objects.get(corporation__corporation_id=corp_id)
    logger.debug("Processing Audit Updates for %s", corp.corporation.corporation_name)
    que = []

    que.append(update_corp_wallet.si(corp_id, force_refresh=force_refresh))

    enqueue_next_task(que)

    logger.debug("Queued Audit Updates for %s", corp.corporation.corporation_name)


@shared_task(
    bind=True,
    base=QueueOnce,
    once={"graceful": False, "keys": ["corp_id"]},
    name="tasks.update_corp_wallet",
)
@no_fail_chain
def update_corp_wallet(
    self, corp_id, force_refresh=False, chain=[]
):  # pylint: disable=unused-argument, dangerous-default-value
    return update_corp_wallet_division(corp_id, force_refresh=force_refresh)


@shared_task(
    bind=True,
    base=QueueOnce,
    once={"graceful": False, "keys": ["character_id"]},
    name="tasks.update_char_mining_ledger",
)
@no_fail_chain
def update_char_mining_ledger(
    self, character_id, force_refresh=False, chain=[]
):  # pylint: disable=unused-argument, dangerous-default-value
    return update_character_mining(character_id, force_refresh=force_refresh)


@shared_task(
    bind=True,
    base=QueueOnce,
    once={"graceful": False, "keys": ["character_id"]},
    name="tasks.update_char_wallet",
)
@no_fail_chain
def update_char_wallet(
    self, character_id, force_refresh=False, chain=[]
):  # pylint: disable=unused-argument, dangerous-default-value
    return update_character_wallet(character_id, force_refresh=force_refresh)


@shared_task(
    bind=True,
    base=QueueOnce,
    once={"graceful": False, "keys": ["character_id"]},
    name="tasks.update_char_planets",
)
@no_fail_chain
def update_char_planets(
    self, character_id, force_refresh=False, chain=[]
):  # pylint: disable=unused-argument, dangerous-default-value
    return update_character_planetary(character_id, force_refresh=force_refresh)


@shared_task(
    bind=True,
    base=QueueOnce,
    once={"graceful": False, "keys": ["character_id", "planet_id"]},
    name="tasks.update_char_planets_details",
)
@no_fail_chain
def update_char_planets_details(
    self, character_id, planet_id, force_refresh=False, chain=[]
):  # pylint: disable=unused-argument, dangerous-default-value
    return update_character_planetary_details(
        character_id, planet_id, force_refresh=force_refresh
    )
