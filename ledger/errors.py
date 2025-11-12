"""Custom exceptions."""

# Alliance Auth
from esi.errors import TokenError


class TokenDoesNotExist(TokenError):
    """A token with a specific scope does not exist for a user."""


class DatabaseError(Exception):
    pass
