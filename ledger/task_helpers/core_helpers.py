"""
Core Helpers
"""

import logging

from esi.models import Token

logger = logging.getLogger(__name__)


def get_token(character_id: int, scopes: list) -> Token:
    """
    Helper method to get a valid token for a specific character with specific scopes.

    Parameters
    ----------
    character_id: `int`
    scopes: `int`

    Returns
    ----------
    `class`: esi.models.Token or False

    """
    token = (
        Token.objects.filter(character_id=character_id)
        .require_scopes(scopes)
        .require_valid()
        .first()
    )
    if token:
        return token
    return False
