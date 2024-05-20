"""App Tasks"""

# Standard Library
import datetime

# Third Party
from celery import shared_task

from django.utils import timezone
from esi.errors import TokenExpiredError
from esi.models import Token

from allianceauth.authentication.models import EveCharacter
from allianceauth.services.tasks import QueueOnce

from ledger.decorators import when_esi_is_available
from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import CharacterAudit
from ledger.models.corporationaudit import CorporationAudit
from ledger.task_helpers.char_helpers import (
    update_character_mining,
    update_character_wallet,
)
from ledger.task_helpers.core_helpers import enqueue_next_task, no_fail_chain
from ledger.task_helpers.corp_helpers import update_corp_wallet_division

logger = get_extension_logger(__name__)

# Character Audit - Tasks


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
            except TokenExpiredError:
                return False
        else:
            logger.info("No Tokens for %s", char_id)
            return False

    logger.debug(
        "Processing Audit Updates for %s", format(character.character.character_name)
    )

    skip_date = timezone.now() - datetime.timedelta(hours=2)
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

    enqueue_next_task(que)

    logger.debug(
        "Queued %s Audit Updates for %s",
        len(que) + 1,
        character.character.character_name,
    )

    return True


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
