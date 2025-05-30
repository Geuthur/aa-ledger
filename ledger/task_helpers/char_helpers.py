"""
Character Helpers
"""

# Standard Library
import logging
from datetime import timedelta

# Django
from django.utils import timezone

# Alliance Auth (External Libs)
from eveuniverse.models import EveType

# AA Ledger
from ledger.decorators import log_timing
from ledger.errors import TokenError
from ledger.models.characteraudit import (
    CharacterAudit,
    CharacterMiningLedger,
    CharacterWalletJournalEntry,
)
from ledger.models.general import EveEntity
from ledger.providers import esi
from ledger.task_helpers.core_helpers import get_token
from ledger.task_helpers.etag_helpers import (
    HTTPGatewayTimeoutError,
    NotModifiedError,
    etag_results,
)

logger = logging.getLogger(__name__)


# pylint: disable=too-many-locals
@log_timing(logger)
def update_character_wallet(character_id, force_refresh=False):
    audit_char = CharacterAudit.objects.get(character__character_id=character_id)
    logger.debug(
        "Updating wallet transactions for: %s", audit_char.character.character_name
    )

    req_scopes = ["esi-wallet.read_character_wallet.v1"]

    token = get_token(character_id, req_scopes)

    if not token:
        logger.info(
            "No Wallet Token for %s",
            audit_char.character.character_name,
        )
        audit_char.is_active()
        return "No Tokens"

    try:
        journal_items_ob = esi.client.Wallet.get_characters_character_id_wallet_journal(
            character_id=character_id
        )

        journal_items = etag_results(
            journal_items_ob, token, force_refresh=force_refresh
        )

        _current_journal = CharacterWalletJournalEntry.objects.filter(
            character=audit_char
        ).values_list(
            "entry_id", flat=True
        )  # TODO add time filter
        _current_eve_ids = list(
            EveEntity.objects.all().values_list("eve_id", flat=True)
        )

        _new_names = []

        items = []
        for item in journal_items:
            if item.get("id") not in _current_journal:
                if item.get("second_party_id") not in _current_eve_ids:
                    _new_names.append(item.get("second_party_id"))
                    _current_eve_ids.append(item.get("second_party_id"))
                if item.get("first_party_id") not in _current_eve_ids:
                    _new_names.append(item.get("first_party_id"))
                    _current_eve_ids.append(item.get("first_party_id"))

                # pylint: disable=duplicate-code
                asset_item = CharacterWalletJournalEntry(
                    character=audit_char,
                    amount=item.get("amount"),
                    balance=item.get("balance"),
                    context_id=item.get("context_id"),
                    context_id_type=item.get("context_id_type"),
                    date=item.get("date"),
                    description=item.get("description"),
                    first_party_id=item.get("first_party_id"),
                    entry_id=item.get("id"),
                    reason=item.get("reason"),
                    ref_type=item.get("ref_type"),
                    second_party_id=item.get("second_party_id"),
                    tax=item.get("tax"),
                    tax_receiver_id=item.get("tax_receiver_id"),
                )
                items.append(asset_item)

        created_names = EveEntity.objects.create_bulk_from_esi(_new_names)

        wallet_ballance = esi.client.Wallet.get_characters_character_id_wallet(
            character_id=character_id, token=token.valid_access_token()
        ).result()

        audit_char.balance = wallet_ballance
        audit_char.save()

        if created_names:
            CharacterWalletJournalEntry.objects.bulk_create(items)
        else:
            raise TokenError("ESI Fail")

        logger.debug(
            "Finished wallet transactions for: %s", audit_char.character.character_name
        )
    except NotModifiedError:
        logger.debug("No New wallet data for: %s", audit_char.character.character_name)
    except HTTPGatewayTimeoutError:
        logger.debug("Gateway Timeout for: %s", audit_char.character.character_name)

    audit_char.last_update_wallet = timezone.now()
    audit_char.save()
    audit_char.is_active()
    return "Success"


@log_timing(logger)
def update_character_mining(character_id, force_refresh=False):
    audit_char = CharacterAudit.objects.get(character__character_id=character_id)
    logger.debug("Updating Mining for: %s", audit_char.character.character_name)

    req_scopes = ["esi-industry.read_character_mining.v1"]

    token = get_token(character_id, req_scopes)

    if not token:
        logger.info(
            "No Mining Token for %s, Deactivate Character",
            audit_char.character.character_name,
        )
        audit_char.is_active()
        return "No Tokens"
    try:
        mining_op = esi.client.Industry.get_characters_character_id_mining(
            character_id=character_id
        )

        ledger = etag_results(mining_op, token, force_refresh=force_refresh)

        existings_pks = set(
            CharacterMiningLedger.objects.filter(
                character=audit_char, date__gte=timezone.now() - timedelta(days=30)
            ).values_list("id", flat=True)
        )
        type_ids = set()
        new_events = []
        old_events = []
        for event in ledger:

            type_ids.add(event.get("type_id"))
            pk = CharacterMiningLedger.create_primary_key(character_id, event)
            _e = CharacterMiningLedger(
                character=audit_char,
                id=pk,
                date=event.get("date"),
                type_id=event.get("type_id"),
                system_id=event.get("solar_system_id"),
                quantity=event.get("quantity"),
            )
            if pk in existings_pks:
                old_events.append(_e)
            else:
                new_events.append(_e)

        EveType.objects.bulk_get_or_create_esi(ids=list(type_ids))

        if new_events:
            CharacterMiningLedger.objects.bulk_create(new_events, ignore_conflicts=True)

        if old_events:
            CharacterMiningLedger.objects.bulk_update(old_events, fields=["quantity"])
        logger.debug("Finished Mining for: %s", audit_char.character.character_name)
    except NotModifiedError:
        logger.debug("No New Mining for: %s", audit_char.character.character_name)
    except HTTPGatewayTimeoutError:
        logger.debug("Gateway Timeout for: %s", audit_char.character.character_name)
        return "Gateway Timeout"

    audit_char.last_update_mining = timezone.now()
    audit_char.save()
    audit_char.is_active()
    return "Success"
