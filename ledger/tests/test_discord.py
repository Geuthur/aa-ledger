# Standard Library
import builtins
from importlib.util import find_spec
from types import SimpleNamespace
from unittest import skipUnless
from unittest.mock import MagicMock, patch

# Third Party
from requests.exceptions import ConnectionError as RequestsConnectionError

# Django
from django.test import modify_settings

# Alliance Auth
from allianceauth.services.modules.discord.models import DiscordUser

# AA Ledger
from ledger.models.general import UserSettings
from ledger.tests import NoSocketsTestCase
from ledger.tests.testdata.factory import UserMainFactory
from ledger.thirdparty import discord as discord_module
from ledger.thirdparty.discord import (
    _discordbot_send_direct_message,
    _discordproxy_send_direct_message,
    _discordwebhook_send_message,
    allianceauth_discordbot_installed,
    discordnotify_installed,
    discordproxy_installed,
    discordwebhook_installed,
    send_user_notification,
    send_webhook_notification,
)

MODULE_PATH = "ledger.thirdparty.discord"
WEBHOOK_URL = "https://discord.com/api/webhooks/1337/abc123"

# aadiscordbot and discordnotify do not support every Alliance Auth version,
# so the test environment of the development version comes without them.
AADISCORDBOT_AVAILABLE = find_spec("aadiscordbot") is not None
DISCORDNOTIFY_AVAILABLE = find_spec("discordnotify") is not None
DISCORDPROXY_AVAILABLE = find_spec("discordproxy") is not None
DHOOKS_LITE_AVAILABLE = find_spec("dhooks_lite") is not None


def _import_without(module_name: str):
    """Return a replacement for `__import__` that fails for the given module."""
    original_import = builtins.__import__

    def import_side_effect(name, globals=None, locals=None, fromlist=(), level=0):
        if name == module_name:
            raise ModuleNotFoundError(f"No module named '{module_name}'")
        return original_import(name, globals, locals, fromlist, level)

    return import_side_effect


def _webhook_response(status_ok: bool):
    return SimpleNamespace(
        status_ok=status_ok,
        status_code=200 if status_ok else 400,
        headers={},
        content={},
    )


class TestModulesInstalled(NoSocketsTestCase):
    @modify_settings(INSTALLED_APPS={"remove": "aadiscordbot"})
    def test_allianceauth_discordbot_installed_should_return_false(self):
        self.assertFalse(allianceauth_discordbot_installed())

    @skipUnless(AADISCORDBOT_AVAILABLE, "aadiscordbot is not installed")
    @modify_settings(INSTALLED_APPS={"append": "aadiscordbot"})
    def test_allianceauth_discordbot_installed_should_return_true(self):
        self.assertTrue(allianceauth_discordbot_installed())

    @modify_settings(INSTALLED_APPS={"remove": "discordnotify"})
    def test_aa_discordnotify_installed_should_return_false(self):
        self.assertFalse(discordnotify_installed())

    @skipUnless(DISCORDNOTIFY_AVAILABLE, "discordnotify is not installed")
    @modify_settings(INSTALLED_APPS={"append": "discordnotify"})
    def test_aa_discordnotify_installed_should_return_true(self):
        self.assertTrue(discordnotify_installed())

    @skipUnless(DISCORDPROXY_AVAILABLE, "discordproxy is not installed")
    def test_discordproxy_installed_should_return_true(self):
        self.assertTrue(discordproxy_installed())

    def test_discordproxy_installed_should_return_false_on_modulenotfounderror(self):
        with patch(
            "builtins.__import__", side_effect=_import_without("discordproxy.client")
        ):
            self.assertFalse(discordproxy_installed())

    @skipUnless(DHOOKS_LITE_AVAILABLE, "dhooks_lite is not installed")
    def test_discordwebhook_installed_should_return_true(self):
        self.assertTrue(discordwebhook_installed())

    def test_discordwebhook_installed_should_return_false_on_modulenotfounderror(self):
        with patch("builtins.__import__", side_effect=_import_without("dhooks_lite")):
            self.assertFalse(discordwebhook_installed())


class TestSendDiscordMessage(NoSocketsTestCase):
    @skipUnless(AADISCORDBOT_AVAILABLE, "aadiscordbot is not installed")
    def test_send_direct_message_with_embed_should_call_send_message_with_embed(self):
        with patch("aadiscordbot.tasks.send_message") as mock_send_message:
            _discordbot_send_direct_message(
                user_id=123456789,
                title="Test Message",
                message="This is a test message.",
                embed_message=True,
                level="info",
            )

        mock_send_message.assert_called_once()
        call_kwargs = mock_send_message.call_args.kwargs

        self.assertEqual(call_kwargs["user_id"], 123456789)
        self.assertEqual(str(call_kwargs["embed"].title), "Test Message")
        self.assertEqual(call_kwargs["embed"].description, "This is a test message.")
        self.assertEqual(
            call_kwargs["embed"].color.value, discord_module.DISCORD_EMBED_COLOR_INFO
        )

    @skipUnless(AADISCORDBOT_AVAILABLE, "aadiscordbot is not installed")
    def test_send_direct_message_without_embed_should_call_send_message_with_text(
        self,
    ):
        with patch("aadiscordbot.tasks.send_message") as mock_send_message:
            _discordbot_send_direct_message(
                user_id=123456789,
                title="Test Message",
                message="This is a test message.",
                embed_message=False,
                level="info",
            )

        mock_send_message.assert_called_once_with(
            user_id=123456789,
            message="**Test Message**\n\nThis is a test message.",
        )

    @skipUnless(DISCORDPROXY_AVAILABLE, "discordproxy is not installed")
    def test_discordproxy_send_direct_message_should_call_create_direct_message(self):
        with patch(
            "discordproxy.client.DiscordClient.create_direct_message"
        ) as mock_create_direct_message:
            _discordproxy_send_direct_message(
                user_id=123456789,
                title="Test Message",
                message="This is a test message.",
                embed_message=True,
                level="info",
            )

        mock_create_direct_message.assert_called_once()
        call_kwargs = mock_create_direct_message.call_args.kwargs

        self.assertEqual(call_kwargs["user_id"], 123456789)
        self.assertEqual(call_kwargs["embed"].title, "Test Message")
        self.assertEqual(call_kwargs["embed"].description, "This is a test message.")

    @skipUnless(DISCORDPROXY_AVAILABLE, "discordproxy is not installed")
    def test_discordproxy_send_direct_message_without_embed_should_send_plain_text(
        self,
    ):
        with patch(
            "discordproxy.client.DiscordClient.create_direct_message"
        ) as mock_create_direct_message:
            _discordproxy_send_direct_message(
                user_id=123456789,
                title="Test Message",
                message="This is a test message.",
                embed_message=False,
                level="info",
            )

        mock_create_direct_message.assert_called_once_with(
            user_id=123456789,
            content="**Test Message**\n\nThis is a test message.",
        )


class TestDiscordWebhookSendMessage(NoSocketsTestCase):
    @patch(MODULE_PATH + ".discordwebhook_installed", return_value=False)
    def test_should_return_none_if_dhooks_lite_is_not_installed(self, _):
        self.assertIsNone(
            _discordwebhook_send_message(
                webhook_url=WEBHOOK_URL, title="Test Title", message="Test Message"
            )
        )

    @skipUnless(DHOOKS_LITE_AVAILABLE, "dhooks_lite is not installed")
    def test_should_send_embed_and_return_true(self):
        with patch("dhooks_lite.Webhook") as mock_webhook:
            mock_webhook.return_value.execute.return_value = _webhook_response(True)

            result = _discordwebhook_send_message(
                webhook_url=WEBHOOK_URL,
                title="Test Title",
                message="Test Message",
                embed_message=True,
                level="warning",
            )

        self.assertTrue(result)
        mock_webhook.assert_called_once_with(url=WEBHOOK_URL)
        embed = mock_webhook.return_value.execute.call_args.kwargs["embeds"][0]
        self.assertEqual(embed.title, "Test Title")
        self.assertEqual(embed.description, "Test Message")
        self.assertEqual(embed.color, discord_module.DISCORD_EMBED_COLOR_WARNING)

    @skipUnless(DHOOKS_LITE_AVAILABLE, "dhooks_lite is not installed")
    def test_should_send_plain_text_and_return_true(self):
        with patch("dhooks_lite.Webhook") as mock_webhook:
            mock_webhook.return_value.execute.return_value = _webhook_response(True)

            result = _discordwebhook_send_message(
                webhook_url=WEBHOOK_URL,
                title="Test Title",
                message="Test Message",
                embed_message=False,
            )

        self.assertTrue(result)
        mock_webhook.return_value.execute.assert_called_once_with(
            content="**Test Title**\n\nTest Message"
        )

    @skipUnless(DHOOKS_LITE_AVAILABLE, "dhooks_lite is not installed")
    def test_should_return_false_if_discord_rejects_the_message(self):
        with patch("dhooks_lite.Webhook") as mock_webhook:
            mock_webhook.return_value.execute.return_value = _webhook_response(False)

            result = _discordwebhook_send_message(
                webhook_url=WEBHOOK_URL, title="Test Title", message="Test Message"
            )

        self.assertFalse(result)

    @skipUnless(DHOOKS_LITE_AVAILABLE, "dhooks_lite is not installed")
    def test_should_return_false_and_not_log_webhook_url_on_request_error(self):
        # The exception text of requests contains the webhook URL with the token.
        with patch("dhooks_lite.Webhook") as mock_webhook:
            mock_webhook.return_value.execute.side_effect = RequestsConnectionError(
                f"Max retries exceeded with url: {WEBHOOK_URL}"
            )

            with self.assertLogs(discord_module.logger.logger, level="DEBUG") as logs:
                result = _discordwebhook_send_message(
                    webhook_url=WEBHOOK_URL, title="Test Title", message="Test Message"
                )

        self.assertFalse(result)
        self.assertEqual(len(logs.records), 1)
        self.assertIn("ConnectionError", logs.records[0].getMessage())
        for record in logs.records:
            self.assertNotIn(WEBHOOK_URL, record.getMessage())
            self.assertNotIn(WEBHOOK_URL, str(record.args))
            self.assertIsNone(record.exc_info)

    @skipUnless(DHOOKS_LITE_AVAILABLE, "dhooks_lite is not installed")
    def test_should_return_false_and_not_raise_on_too_long_content(self):
        # dhooks_lite raises ValueError before a request is sent. Raised from a
        # Celery task, the task arguments with the webhook URL would end up in
        # the log record.
        with self.assertLogs(discord_module.logger.logger, level="DEBUG") as logs:
            result = _discordwebhook_send_message(
                webhook_url=WEBHOOK_URL,
                title="Test Title",
                message="x" * 2001,
                embed_message=False,
            )

        self.assertFalse(result)
        self.assertEqual(len(logs.records), 1)
        self.assertIn("ValueError", logs.records[0].getMessage())
        for record in logs.records:
            self.assertNotIn(WEBHOOK_URL, record.getMessage())
            self.assertNotIn(WEBHOOK_URL, str(record.args))
            self.assertIsNone(record.exc_info)

    @skipUnless(DHOOKS_LITE_AVAILABLE, "dhooks_lite is not installed")
    def test_should_return_false_and_not_raise_on_type_error(self):
        with patch("dhooks_lite.Webhook") as mock_webhook:
            mock_webhook.return_value.execute.side_effect = TypeError(
                "embeds elements must be of type Embed"
            )

            with self.assertLogs(discord_module.logger.logger, level="DEBUG") as logs:
                result = _discordwebhook_send_message(
                    webhook_url=WEBHOOK_URL, title="Test Title", message="Test Message"
                )

        self.assertFalse(result)
        self.assertEqual(len(logs.records), 1)
        self.assertIn("TypeError", logs.records[0].getMessage())
        for record in logs.records:
            self.assertNotIn(WEBHOOK_URL, record.getMessage())
            self.assertNotIn(WEBHOOK_URL, str(record.args))
            self.assertIsNone(record.exc_info)


class TestSendUserNotification(NoSocketsTestCase):
    def setUp(self):
        # These tests cover the choice of the sender and use stand-in users, so
        # the lookup of `UserSettings` is replaced. `TestSendUserNotificationSettings`
        # checks `disable_notifications` with real rows.
        patcher = patch(MODULE_PATH + ".UserSettings")
        self.mock_user_settings = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_user_settings.objects.filter.return_value.exists.return_value = False

    @patch(MODULE_PATH + ".notify")
    @patch(MODULE_PATH + ".logger.warning")
    @patch(MODULE_PATH + ".User.objects.get")
    def test_send_user_notification_should_return_if_user_not_exists(
        self, mock_get_user, mock_logger_warning, mock_notify
    ):
        mock_get_user.side_effect = discord_module.User.DoesNotExist

        send_user_notification(
            user_id=123,
            title="Test Title",
            message="Test Message",
            embed_message=True,
            level="info",
        )

        mock_logger_warning.assert_called_once_with(
            "User with ID %s does not exist. Notification not sent.", 123
        )
        mock_notify.info.assert_not_called()

    @patch(MODULE_PATH + "._discordproxy_send_direct_message")
    @patch(MODULE_PATH + "._discordbot_send_direct_message")
    @patch(MODULE_PATH + ".notify")
    @patch(MODULE_PATH + ".User.objects.get")
    def test_send_user_notification_should_only_notify_if_user_has_no_discord(
        self,
        mock_get_user,
        mock_notify,
        mock_send_discordbot,
        mock_send_discordproxy,
    ):
        user = SimpleNamespace(username="tester")
        mock_get_user.return_value = user

        send_user_notification(
            user_id=123,
            title="Test Title",
            message="Test Message",
            embed_message=True,
            level="info",
        )

        mock_notify.info.assert_called_once_with(
            user=user, title="Test Title", message="Test Message"
        )
        mock_send_discordbot.assert_not_called()
        mock_send_discordproxy.assert_not_called()

    @patch(MODULE_PATH + "._discordproxy_send_direct_message")
    @patch(MODULE_PATH + "._discordbot_send_direct_message")
    @patch(MODULE_PATH + ".allianceauth_discordbot_installed", return_value=True)
    @patch(MODULE_PATH + ".notify")
    @patch(MODULE_PATH + ".User.objects.get")
    def test_send_user_notification_should_use_discordbot_if_installed(
        self,
        mock_get_user,
        mock_notify,
        _,
        mock_send_discordbot,
        mock_send_discordproxy,
    ):
        user = SimpleNamespace(
            username="tester", discord=SimpleNamespace(uid="123456789")
        )
        mock_get_user.return_value = user

        send_user_notification(
            user_id=123,
            title="Test Title",
            message="Test Message",
            embed_message=False,
            level="warning",
        )

        mock_notify.warning.assert_called_once_with(
            user=user, title="Test Title", message="Test Message"
        )
        mock_send_discordbot.assert_called_once_with(
            user_id=123456789,
            title="Test Title",
            message="Test Message",
            embed_message=False,
            level="warning",
        )
        mock_send_discordproxy.assert_not_called()

    @patch(MODULE_PATH + "._discordproxy_send_direct_message")
    @patch(MODULE_PATH + "._discordbot_send_direct_message")
    @patch(MODULE_PATH + ".discordproxy_installed", return_value=True)
    @patch(MODULE_PATH + ".discordnotify_installed", return_value=False)
    @patch(MODULE_PATH + ".allianceauth_discordbot_installed", return_value=False)
    @patch(MODULE_PATH + ".notify")
    @patch(MODULE_PATH + ".User.objects.get")
    def test_send_user_notification_should_use_discordproxy_if_available(
        self,
        mock_get_user,
        mock_notify,
        _discordbot_installed,
        _discordnotify_installed,
        _discordproxy_installed,
        mock_send_discordbot,
        mock_send_discordproxy,
    ):
        user = SimpleNamespace(
            username="tester", discord=SimpleNamespace(uid="123456789")
        )
        mock_get_user.return_value = user

        send_user_notification(
            user_id=123,
            title="Test Title",
            message="Test Message",
            embed_message=True,
            level="info",
        )

        mock_notify.info.assert_called_once_with(
            user=user, title="Test Title", message="Test Message"
        )
        mock_send_discordproxy.assert_called_once_with(
            user_id=123456789,
            title="Test Title",
            message="Test Message",
            embed_message=True,
            level="info",
        )
        mock_send_discordbot.assert_not_called()

    @patch(MODULE_PATH + "._discordproxy_send_direct_message")
    @patch(MODULE_PATH + "._discordbot_send_direct_message")
    @patch(MODULE_PATH + ".discordproxy_installed", return_value=False)
    @patch(MODULE_PATH + ".discordnotify_installed", return_value=False)
    @patch(MODULE_PATH + ".allianceauth_discordbot_installed", return_value=False)
    @patch(MODULE_PATH + ".notify")
    @patch(MODULE_PATH + ".User.objects.get")
    def test_send_user_notification_should_not_send_discord_message_when_discordproxy_unavailable(
        self,
        mock_get_user,
        mock_notify,
        _discordbot_installed,
        _discordnotify_installed,
        _discordproxy_installed,
        mock_send_discordbot,
        mock_send_discordproxy,
    ):
        user = SimpleNamespace(
            username="tester", discord=SimpleNamespace(uid="123456789")
        )
        mock_get_user.return_value = user

        send_user_notification(
            user_id=123,
            title="Test Title",
            message="Test Message",
            embed_message=True,
            level="info",
        )

        mock_notify.info.assert_called_once_with(
            user=user, title="Test Title", message="Test Message"
        )
        mock_send_discordbot.assert_not_called()
        mock_send_discordproxy.assert_not_called()

    @patch(MODULE_PATH + "._discordproxy_send_direct_message")
    @patch(MODULE_PATH + "._discordbot_send_direct_message")
    @patch(MODULE_PATH + ".discordnotify_installed", return_value=True)
    @patch(MODULE_PATH + ".allianceauth_discordbot_installed", return_value=False)
    @patch(MODULE_PATH + ".notify")
    @patch(MODULE_PATH + ".User.objects.get")
    def test_send_user_notification_should_leave_discord_message_to_discordnotify(
        self,
        mock_get_user,
        mock_notify,
        _discordbot_installed,
        _discordnotify_installed,
        mock_send_discordbot,
        mock_send_discordproxy,
    ):
        user = SimpleNamespace(
            username="tester", discord=SimpleNamespace(uid="123456789")
        )
        mock_get_user.return_value = user

        send_user_notification(
            user_id=123,
            title="Test Title",
            message="Test Message",
            embed_message=True,
            level="info",
        )

        mock_notify.info.assert_called_once_with(
            user=user, title="Test Title", message="Test Message"
        )
        mock_send_discordbot.assert_not_called()
        mock_send_discordproxy.assert_not_called()


@patch(MODULE_PATH + "._discordproxy_send_direct_message")
@patch(MODULE_PATH + "._discordbot_send_direct_message")
@patch(MODULE_PATH + ".allianceauth_discordbot_installed", return_value=True)
@patch(MODULE_PATH + ".notify")
class TestSendUserNotificationSettings(NoSocketsTestCase):
    """`disable_notifications` with real rows of `UserSettings`."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory()
        DiscordUser.objects.create(user=cls.user, uid=123456789)

    def _send(self):
        send_user_notification(
            user_id=self.user.pk,
            title="Test Title",
            message="Test Message",
            embed_message=True,
            level="info",
        )

    def _assert_sent(self, mock_notify, mock_send_discordbot):
        mock_notify.info.assert_called_once_with(
            user=self.user, title="Test Title", message="Test Message"
        )
        mock_send_discordbot.assert_called_once_with(
            user_id=123456789,
            title="Test Title",
            message="Test Message",
            embed_message=True,
            level="info",
        )

    def test_should_send_nothing_if_notifications_disabled(
        self, mock_notify, _, mock_send_discordbot, mock_send_discordproxy
    ):
        UserSettings.objects.create(user=self.user, disable_notifications=True)

        self._send()

        mock_notify.info.assert_not_called()
        mock_send_discordbot.assert_not_called()
        mock_send_discordproxy.assert_not_called()

    def test_should_send_if_user_has_no_settings(
        self, mock_notify, _, mock_send_discordbot, mock_send_discordproxy
    ):
        self.assertFalse(UserSettings.objects.filter(user=self.user).exists())

        self._send()

        self._assert_sent(mock_notify, mock_send_discordbot)
        mock_send_discordproxy.assert_not_called()

    def test_should_send_if_notifications_not_disabled(
        self, mock_notify, _, mock_send_discordbot, mock_send_discordproxy
    ):
        UserSettings.objects.create(user=self.user, disable_notifications=False)

        self._send()

        self._assert_sent(mock_notify, mock_send_discordbot)
        mock_send_discordproxy.assert_not_called()

    def test_should_ignore_disabled_notifications_of_other_users(
        self, mock_notify, _, mock_send_discordbot, mock_send_discordproxy
    ):
        UserSettings.objects.create(user=UserMainFactory(), disable_notifications=True)

        self._send()

        self._assert_sent(mock_notify, mock_send_discordbot)
        mock_send_discordproxy.assert_not_called()


class TestSendWebhookNotification(NoSocketsTestCase):
    @patch(MODULE_PATH + "._discordwebhook_send_message")
    def test_should_not_send_without_webhook_url(self, mock_send_message):
        send_webhook_notification(
            webhook_url=None, title="Test Title", message="Test Message"
        )

        mock_send_message.assert_not_called()

    @patch(MODULE_PATH + ".send_webhook_notification.retry")
    @patch(MODULE_PATH + "._discordwebhook_send_message", return_value=True)
    def test_should_send_and_not_retry_on_success(self, mock_send_message, mock_retry):
        send_webhook_notification(
            webhook_url=WEBHOOK_URL,
            title="Test Title",
            message="Test Message",
            embed_message=False,
            level="danger",
        )

        mock_send_message.assert_called_once_with(
            webhook_url=WEBHOOK_URL,
            title="Test Title",
            message="Test Message",
            embed_message=False,
            level="danger",
        )
        mock_retry.assert_not_called()

    @patch(MODULE_PATH + ".send_webhook_notification.retry")
    @patch(MODULE_PATH + ".discordwebhook_installed", return_value=False)
    def test_should_not_retry_if_dhooks_lite_is_not_installed(self, _, mock_retry):
        send_webhook_notification(
            webhook_url=WEBHOOK_URL, title="Test Title", message="Test Message"
        )

        mock_retry.assert_not_called()

    @patch(MODULE_PATH + ".send_webhook_notification.retry")
    @patch(MODULE_PATH + "._discordwebhook_send_message", return_value=False)
    def test_should_retry_if_sending_failed(self, _, mock_retry: MagicMock):
        send_webhook_notification(
            webhook_url=WEBHOOK_URL, title="Test Title", message="Test Message"
        )

        mock_retry.assert_called_once_with(
            args=[WEBHOOK_URL, "Test Title", "Test Message", True, "info"],
            countdown=2,
            max_retries=3,
        )

    @patch(MODULE_PATH + ".send_webhook_notification.retry")
    @patch(MODULE_PATH + "._discordwebhook_send_message", return_value=False)
    def test_should_not_log_webhook_url_if_sending_failed(self, _, __):
        # The webhook URL contains the token and must not end up in the log.
        with self.assertLogs(discord_module.logger.logger, level="DEBUG") as logs:
            send_webhook_notification(
                webhook_url=WEBHOOK_URL, title="Test Title", message="Test Message"
            )

        self.assertEqual(len(logs.records), 1)
        for record in logs.records:
            self.assertNotIn(WEBHOOK_URL, record.getMessage())
            self.assertNotIn(WEBHOOK_URL, str(record.args))

    @patch(MODULE_PATH + "._discordwebhook_send_message", return_value=False)
    def test_should_not_raise_or_log_webhook_url_if_retries_are_exhausted(self, _):
        # Celery puts the task arguments, and with them the webhook URL, into
        # the text of `MaxRetriesExceededError`. `retries=3` runs the task as
        # the last retry, so the real `retry()` of Celery raises it.
        with self.assertLogs(level="DEBUG") as logs:
            result = send_webhook_notification.apply(
                kwargs={
                    "webhook_url": WEBHOOK_URL,
                    "title": "Test Title",
                    "message": "Test Message",
                },
                retries=3,
                throw=False,
            )

        self.assertEqual(result.state, "SUCCESS")
        messages = [record.getMessage() for record in logs.records]
        self.assertTrue(
            any("after the maximum number of retries" in msg for msg in messages)
        )
        # Only the written message is checked: the record of Celery for a
        # finished task carries the task arguments as data without writing them.
        for record in logs.records:
            self.assertNotIn(WEBHOOK_URL, record.getMessage())
            self.assertIsNone(record.exc_info)
