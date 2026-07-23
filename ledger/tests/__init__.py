# Standard Library
import socket
from unittest.mock import Mock

# Django
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.handlers.wsgi import WSGIRequest
from django.test import RequestFactory, TestCase
from django.urls import reverse

# AA Ledger
from ledger.tests.testdata.factory import UserMainFactory
from ledger.views.alliance.add_ally import add_ally
from ledger.views.character.add_char import add_char
from ledger.views.corporation.add_corp import add_corp


class SocketAccessError(Exception):
    """Error raised when a test script accesses the network"""


class NoSocketsTestCase(TestCase):
    """Variation of Django's TestCase class that prevents any network use.

    Example:

        .. code-block:: python

            class TestMyStuff(BaseTestCase):
                def test_should_do_what_i_need(self): ...

    """

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


class LedgerTestCase(NoSocketsTestCase):
    """
    Preloaded Testcase class for Ledger tests without Network access.

    Pre-Load:
        * Alliance Auth Characters, Corporation, Alliance Data
        * Eve Entity Data
        * Taken User IDs: 1001, 1002, 1003, 1004, 1005

    Available Request Factory:
        `self.factory`

    Available test users:
        * `user` User with standard Ledger access.
            * 'ledger.basic_access' Permission
            * Character ID 1001
            * Corporation ID 2001
            * Alliance ID 3001
        * `user2` Second user with standard Ledger access.
            * 'ledger.basic_access' Permission
            * Character ID 1002
            * Corporation ID 2002
            * Alliance ID 3002
        * `superuser` Superuser.
            * Access to whole Application
            * Character ID 1003
        * `manage_own_user` User with manage own corporation access.
            * 'ledger.basic_access' Permission
            * 'ledger.advanced_access' Permission
            * 'ledger.corp_audit_manager' Permission
            * 'ledger.manage_access' Permission
            * Character ID 1004
            * Corporation ID 2001
            * Alliance ID 3001
        * `manage_user` User with manage corporations access.
            * 'ledger.basic_access' Permission
            * 'ledger.advanced_access' Permission
            * 'ledger.corp_audit_admin_manager' Permission
            * 'ledger.manage_access' Permission
            * Character ID 1005
            * Corporation ID 2001
            * Alliance ID 3001

    Example:
        .. code-block:: python

            class TestMyLedgerStuff(LedgerTestCase):
                def test_should_do_what_i_need(self):
                    user = self.user
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Request Factory
        cls.factory = RequestFactory()

        # User with Standard Access - Corporation 2001 - Alliance 3001
        cls.user = UserMainFactory()
        cls.user_character = cls.user.profile.main_character
        # User with Standard Access - Corporation 2002 - Alliance 3002
        cls.user2 = UserMainFactory()
        cls.user2_character = cls.user2.profile.main_character
        # User with Superuser Access - Corporation 2003 - Alliance 3003
        cls.superuser = UserMainFactory()
        cls.superuser_character = cls.superuser.profile.main_character
        cls.superuser.is_superuser = True
        cls.superuser.save()
        # User with Manage Own Corporation Access - Corporation 2001 - Alliance 3001
        cls.manage_own_user = UserMainFactory(
            permissions__=[
                "ledger.basic_access",
                "ledger.advanced_access",
                "ledger.corp_audit_manager",
                "ledger.manage_access",
            ]
        )
        cls.manage_own_character = cls.manage_own_user.profile.main_character
        # User with Manage Corporations Access - Corporation 2001 - Alliance 3001
        cls.manage_user = UserMainFactory(
            permissions__=[
                "ledger.basic_access",
                "ledger.advanced_access",
                "ledger.corp_audit_admin_manager",
                "ledger.manage_access",
            ]
        )
        cls.manage_character = cls.manage_user.profile.main_character

    def _add_character(self, user, token):
        request = self.factory.get(reverse("ledger:add_char"))
        request.user = user
        request.token = token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        orig_view = add_char.__wrapped__.__wrapped__.__wrapped__
        return orig_view(request, token)

    def _add_corporation(self, user, token):
        request = self.factory.get(reverse("ledger:add_corp"))
        request.user = user
        request.token = token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        orig_view = add_corp.__wrapped__.__wrapped__.__wrapped__
        return orig_view(request, token)

    def _add_alliance(self, user, token):
        request = self.factory.get(reverse("ledger:add_ally"))
        request.user = user
        request.token = token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        orig_view = add_ally.__wrapped__.__wrapped__.__wrapped__
        return orig_view(request, token)

    def _middleware_process_request(self, request: WSGIRequest):
        """Helper method to process middleware for a request."""
        session_middleware = SessionMiddleware(Mock())
        session_middleware.process_request(request)
        message_middleware = MessageMiddleware(Mock())
        message_middleware.process_request(request)
