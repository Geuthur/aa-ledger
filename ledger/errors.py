"""Custom exceptions."""

# Alliance Auth
from esi.errors import TokenError


class TokenDoesNotExist(TokenError):
    """A token with a specific scope does not exist for a user."""


class DatabaseError(Exception):
    """Custom exception to indicate a database error."""


class DownTimeError(Exception):
    """Custom exception to indicate ESI is in daily downtime."""
