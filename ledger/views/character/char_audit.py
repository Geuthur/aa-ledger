"""
Character Audit
"""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from esi.decorators import token_required

from allianceauth.eveonline.models import EveCharacter

from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import CharacterAudit
from ledger.tasks import update_character

logger = get_extension_logger(__name__)


@login_required
@token_required(scopes=CharacterAudit.get_esi_scopes())
def add_char(request, token):
    CharacterAudit.objects.update_or_create(
        character=EveCharacter.objects.get_character_by_id(token.character_id)
    )
    update_character.apply_async(
        args=[token.character_id], kwargs={"force_refresh": True}, priority=6
    )
    msg = "Char successfully added/updated to Ledger"
    messages.info(request, msg)
    return render(request, "ledger/ledger/index.html")


@login_required
@permission_required(["ledger.admin_access", "ledger.char_audit_admin_access"])
def fetch_memberaudit(request):
    """Add All Chars from Memberaudit to CharacterAudit"""
    try:
        # pylint: disable=import-outside-toplevel
        from memberaudit.models import Character

        from django.utils import timezone

        chars = Character.objects.filter(is_disabled=0)
        count = 0

        # Zeitlimit für den letzten Wallet-Update (2 Stunden)
        time_limit = timezone.now() - timedelta(hours=2)

        for char in chars:
            char_audit, _ = CharacterAudit.objects.get_or_create(
                character=char.eve_character,
                id=char.id,
            )
            if char_audit:
                if (
                    not char_audit.last_update_wallet
                    or char_audit.last_update_wallet < time_limit
                ):
                    update_character.apply_async(
                        args=[char.eve_character.character_id],
                        kwargs={"force_refresh": True},
                        priority=6,
                    )
                    count += 1
                else:
                    continue
        msg = (
            f"{count} Char(s) successfully added/updated to Ledger"
            if count
            else "No Updates initialized."
        )
        messages.info(request, msg)
    except ImportError:
        msg = (
            "The 'memberaudit' app is not installed. Please make sure it is installed."
        )
        messages.error(request, msg)

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(e, exc_info=True)
        msg = "An error occurred: Please inform your Admin."
        messages.error(request, msg)

    return render(request, "ledger/ledger/index.html")
