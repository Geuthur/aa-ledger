"""Custom exceptions."""

# Alliance Auth
from esi.errors import TokenError


class NotModifiedError(Exception):
    pass


class HTTPGatewayTimeoutError(Exception):
    pass


class TokenDoesNotExist(TokenError):
    """A token with a specific scope does not exist for a user."""


class MemberNotActive(Exception):
    pass


class DatabaseError(Exception):
    pass


class ESSError(Exception):
    pass


class CustomError(Exception):
    pass


class LedgerImportError(Exception):
    pass
