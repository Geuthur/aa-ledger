"""
Corporation Helpers
"""

from django.utils import timezone
from esi.errors import TokenError
from esi.models import Token

from allianceauth.eveonline.models import EveCharacter

from ledger.decorators import log_timing
from ledger.errors import DatabaseError
from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
)
from ledger.models.general import EveEntity
from ledger.providers import esi
from ledger.task_helpers.etag_helpers import NotModifiedError, etag_results

logger = get_extension_logger(__name__)


def get_corp_token(corp_id, scopes, req_roles):
    """
    Helper method to get a token for a specific character from a specific corp with specific scopes

    Parameters
    ----------
    corp_id: `int`
    scopes: `int`
    req_roles: `list`

    Returns
    ----------
    `class`: esi.models.Token or False

    """
    if "esi-characters.read_corporation_roles.v1" not in scopes:
        scopes.append("esi-characters.read_corporation_roles.v1")

    char_ids = EveCharacter.objects.filter(corporation_id=corp_id).values(
        "character_id"
    )
    tokens = Token.objects.filter(character_id__in=char_ids).require_scopes(scopes)

    for token in tokens:
        try:
            roles = esi.client.Character.get_characters_character_id_roles(
                character_id=token.character_id, token=token.valid_access_token()
            ).result()

            has_roles = False
            for role in roles.get("roles", []):
                if role in req_roles:
                    has_roles = True

            if has_roles:
                return token
        except TokenError as e:
            logger.error(
                "Token ID: %s (%s)",
                token.pk,
                e,
            )
    return False


@log_timing(logger)
def update_corp_wallet_division(corp_id, force_refresh=False):
    audit_corp = CorporationAudit.objects.get(corporation__corporation_id=corp_id)

    req_scopes = [
        "esi-wallet.read_corporation_wallets.v1",
        "esi-characters.read_corporation_roles.v1",
        "esi-corporations.read_divisions.v1",
    ]
    req_roles = ["CEO", "Director"]

    token = get_corp_token(corp_id, req_scopes, req_roles)
    names = {}

    if token:
        division_names = (
            esi.client.Corporation.get_corporations_corporation_id_divisions(
                corporation_id=audit_corp.corporation.corporation_id,
                token=token.valid_access_token(),
            ).result()
        )

        for division in division_names.get("wallet"):
            names[division.get("division")] = division.get("name")

    req_roles = ["CEO", "Director", "Accountant", "Junior_Accountant"]

    token = get_corp_token(corp_id, req_scopes, req_roles)

    if not token:
        return "No Tokens"

    try:
        divisions_items_ob = esi.client.Wallet.get_corporations_corporation_id_wallets(
            corporation_id=audit_corp.corporation.corporation_id
        )

        division_items = etag_results(
            divisions_items_ob, token, force_refresh=force_refresh
        )

        for division in division_items:
            _division_item, _ = CorporationWalletDivision.objects.update_or_create(
                corporation=audit_corp,
                division=division.get("division"),
                defaults={
                    "balance": division.get("balance"),
                    "name": names.get(division.get("division"), "Unknown"),
                },
            )

            if _division_item:
                update_corp_wallet_journal(
                    corp_id, division.get("division"), force_refresh=force_refresh
                )  # inline not async

    except NotModifiedError:
        logger.debug(
            "No New wallet data for: %s",
            audit_corp.corporation.corporation_name,
        )

    audit_corp.last_update_wallet = timezone.now()
    audit_corp.save()

    return ("Finished wallet divs for: %s", audit_corp.corporation.corporation_name)


# pylint: disable=too-many-locals
def update_corp_wallet_journal(corp_id, wallet_division, force_refresh=False):
    audit_corp = CorporationAudit.objects.get(corporation__corporation_id=corp_id)

    division = CorporationWalletDivision.objects.get(
        corporation=audit_corp, division=wallet_division
    )

    logger.debug(
        "Updating wallet transactions for: %s (Div: %s)",
        audit_corp.corporation.corporation_name,
        division,
    )

    req_scopes = [
        "esi-wallet.read_corporation_wallets.v1",
        "esi-characters.read_corporation_roles.v1",
    ]

    req_roles = ["CEO", "Director", "Accountant", "Junior_Accountant"]

    token = get_corp_token(corp_id, req_scopes, req_roles)

    if not token:
        return "No Tokens"

    try:
        _current_journal = set(
            list(
                CorporationWalletJournalEntry.objects.filter(division=division)
                .order_by("-date")
                .values_list("entry_id", flat=True)[:20000]
            )
        )
        _current_eve_ids = set(
            list(EveEntity.objects.all().values_list("eve_id", flat=True))
        )

        current_page = 1
        total_pages = 1
        _new_names = []
        while current_page <= total_pages:
            journal_items_ob = esi.client.Wallet.get_corporations_corporation_id_wallets_division_journal(
                corporation_id=audit_corp.corporation.corporation_id,
                division=wallet_division,
                page=current_page,
            )
            journal_items = etag_results(
                journal_items_ob, token, force_refresh=force_refresh
            )

            _min_time = timezone.now()
            items = []
            for item in journal_items:
                _min_time = min(_min_time, item.get("date"))

                if item.get("id") not in _current_journal:
                    if item.get("second_party_id") not in _current_eve_ids:
                        _new_names.append(item.get("second_party_id"))
                        _current_eve_ids.add(item.get("second_party_id"))
                    if item.get("first_party_id") not in _current_eve_ids:
                        _new_names.append(item.get("first_party_id"))
                        _current_eve_ids.add(item.get("first_party_id"))

                    wallet_item = (
                        CorporationWalletJournalEntry(  # pylint: disable=duplicate-code
                            division=division,
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
                    )

                    items.append(wallet_item)

            logger.debug(
                "Corp %s Div %s, Page: %s, New Transactions! {len(items)}, New Names {_new_names}",
                corp_id,
                wallet_division,
                current_page,
            )
            created_names = EveEntity.objects.create_bulk_from_esi(_new_names)

            if created_names:
                CorporationWalletJournalEntry.objects.bulk_create(items)
            else:
                raise DatabaseError("DB Fail")

            current_page += 1
    except NotModifiedError:
        logger.debug(
            "No New wallet data for: Div: %s Corp: %s",
            audit_corp.corporation.corporation_name,
            wallet_division,
        )
    return True
