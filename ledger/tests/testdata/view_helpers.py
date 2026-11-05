# Standard Library
from unittest.mock import Mock

# Django
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse

# AA Ledger
from ledger.views import add_ally, add_char, add_corp


def _call_wrapped_view(factory, view, url_name, user, token):
    """Call the view without its decorators, with a session-enabled request."""
    request = factory.get(reverse(url_name))
    request.user = user
    request.token = token
    middleware = SessionMiddleware(Mock())
    middleware.process_request(request)
    return view.__wrapped__.__wrapped__.__wrapped__(request, token)


def add_character(factory, user, token):
    return _call_wrapped_view(factory, add_char, "ledger:add_char", user, token)


def add_corporation(factory, user, token):
    return _call_wrapped_view(factory, add_corp, "ledger:add_corp", user, token)


def add_alliance(factory, user, token):
    return _call_wrapped_view(factory, add_ally, "ledger:add_ally", user, token)
