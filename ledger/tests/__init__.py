# Standard Library
import socket
from unittest.mock import Mock

# Django
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.handlers.wsgi import WSGIRequest
from django.test import RequestFactory, TestCase

# AA Ledger
from ledger.tests.testdata.factory import UserMainFactory


class SocketAccessError(Exception):
    """Error raised when a test script accesses the network"""


class NoSocketsTestCase(TestCase):
    """Variation of Django's TestCase class that prevents any network use."""

    @classmethod
    def setUpClass(cls):
        cls.socket_original = socket.socket
        socket.socket = cls.guard
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        socket.socket = cls.socket_original
        return super().tearDownClass()

    @staticmethod
    def guard(*args, **kwargs):
        raise SocketAccessError("Attempted to access network")


class AuthTestCase(NoSocketsTestCase):
    """
    Preloaded Testcase class for AllianceAuth tests without Network access.

    Available Request Factory:
        `self.factory`
    Available Django Users:
        `self.user`
        `self.superuser`
    Available methods:
        `_middleware_process_request(request)`
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Request Factory
        cls.factory = RequestFactory()

        # User with Standard Access
        cls.user = UserMainFactory()

        # User with Superuser Access
        cls.superuser = UserMainFactory()
        cls.superuser.is_superuser = True
        cls.superuser.save()

    def _middleware_process_request(self, request: WSGIRequest):
        """Helper method to process middleware for a request."""
        session_middleware = SessionMiddleware(Mock())
        session_middleware.process_request(request)
        message_middleware = MessageMiddleware(Mock())
        message_middleware.process_request(request)
