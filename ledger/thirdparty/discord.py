"""Discord notifications via Alliance Auth, aadiscordbot, discordproxy or a webhook."""

# Third Party
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from requests.exceptions import RequestException

# Django
from django.apps import apps
from django.utils import timezone

# Alliance Auth
from allianceauth.authentication.models import User
from allianceauth.notifications import notify

# AA Ledger
from ledger import __title__
from ledger.models.general import UserSettings
from ledger.providers import logger

# Embed colors
DISCORD_EMBED_COLOR_INFO = 0x5BC0DE
DISCORD_EMBED_COLOR_SUCCESS = 0x5CB85C
DISCORD_EMBED_COLOR_WARNING = 0xF0AD4E
DISCORD_EMBED_COLOR_DANGER = 0xD9534F

# Discord embed color map
DISCORD_EMBED_COLOR_MAP = {
    "info": DISCORD_EMBED_COLOR_INFO,
    "success": DISCORD_EMBED_COLOR_SUCCESS,
    "warning": DISCORD_EMBED_COLOR_WARNING,
    "danger": DISCORD_EMBED_COLOR_DANGER,
}


def allianceauth_discordbot_installed() -> bool:
    return apps.is_installed(app_name="aadiscordbot")


def discordnotify_installed() -> bool:
    return apps.is_installed(app_name="discordnotify")


# pylint: disable=import-outside-toplevel, unused-import
def discordproxy_installed() -> bool:
    try:
        # Third Party
        from discordproxy.client import DiscordClient
    except ModuleNotFoundError:
        return False
    return True


# pylint: disable=import-outside-toplevel, unused-import
def discordwebhook_installed() -> bool:
    try:
        # Third Party
        import dhooks_lite
    except ModuleNotFoundError:
        return False
    return True


# pylint: disable=import-outside-toplevel, import-self, no-name-in-module
def _discordbot_send_direct_message(
    user_id: int,
    title: str,
    message: str,
    embed_message: bool = True,
    level: str = "info",
) -> None:
    """Send a private message to a user via discordbot"""

    # Third Party
    from aadiscordbot.tasks import send_message
    from discord import Embed

    embed = Embed(
        title=str(title),
        description=message,
        color=DISCORD_EMBED_COLOR_MAP.get(level),
        timestamp=timezone.now(),
    )

    if embed_message is True:
        send_message(user_id=user_id, embed=embed)
    else:
        send_message(user_id=user_id, message=f"**{title}**\n\n{message}")


def _discordproxy_send_direct_message(
    user_id: int,
    title: str,
    message: str,
    embed_message: bool = True,
    level: str = "info",
):
    """Send a direct message to a user via discordproxy"""
    # Third Party
    from discordproxy.client import DiscordClient

    client = DiscordClient()
    if embed_message is True:
        # Third Party
        from discordproxy.discord_api_pb2 import Embed

        footer = Embed.Footer(text=str(__title__))
        embed = Embed(
            title=str(title),
            description=message,
            color=DISCORD_EMBED_COLOR_MAP.get(level),
            timestamp=timezone.now().isoformat(),
            footer=footer,
        )

        client.create_direct_message(user_id=user_id, embed=embed)
    else:
        client.create_direct_message(
            user_id=user_id, content=f"**{title}**\n\n{message}"
        )


def _discordwebhook_send_message(
    webhook_url: str,
    title: str,
    message: str,
    embed_message: bool = True,
    level: str = "info",
) -> bool | None:
    """Send a message to a webhook via discordwebhook

    Returns `True` if the message was sent, `False` if sending failed and a
    retry makes sense, and `None` if it was not sent and a retry cannot help
    (dhooks_lite is not installed or rejects the message).
    """
    if not discordwebhook_installed():
        logger.debug(
            "Discord webhook is not installed, messages will not be sent via webhook."
        )
        return None

    # Third Party
    import dhooks_lite

    hook = dhooks_lite.Webhook(url=webhook_url)
    try:
        if embed_message is True:
            # Third Party
            from dhooks_lite import Embed

            embed = Embed(
                title=str(title),
                description=message,
                color=DISCORD_EMBED_COLOR_MAP.get(level),
                timestamp=timezone.now(),
            )
            response = hook.execute(embeds=[embed])
        else:
            response = hook.execute(content=f"**{title}**\n\n{message}")
    except RequestException as exc:
        # The text of a RequestException contains the webhook URL with the
        # token, and Celery attaches the task arguments with the URL to its
        # log record. So only the type of the exception is logged.
        logger.warning(
            "Webhook failed to send message to Discord. Error: %s",
            type(exc).__name__,
        )
        return False
    except (ValueError, TypeError) as exc:
        # dhooks_lite rejects the message (e.g. content over 2000 characters)
        # before any request is sent, so a retry can never help. The exception
        # is not raised and only its type is logged, for the same reason as
        # above.
        logger.warning(
            "Webhook message was rejected by dhooks_lite and is not sent. Error: %s",
            type(exc).__name__,
        )
        return None

    logger.debug("headers: %s", response.headers)
    logger.debug("status_code: %s", response.status_code)
    logger.debug("content: %s", response.content)

    if not response.status_ok:
        msg = (
            f"Webhook failed to send message to Discord. "
            f"HTTP status code: {response.status_code}. "
            f"API response: {response.content}"
        )
        logger.warning(msg)
        return False
    return True


@shared_task
def send_user_notification(
    user_id: int,
    title: str,
    message: str,
    embed_message: bool = True,
    level: str = "info",
) -> None:
    """Send a notification as a Celery Task to a user via Discord or AllianceAuth notify."""
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning(
            "User with ID %s does not exist. Notification not sent.", user_id
        )
        return

    if UserSettings.objects.filter(user=user, disable_notifications=True).exists():
        logger.info("Notifications are disabled for user %s; skipping delivery.", user)
        return

    getattr(notify, level)(user=user, title=title, message=message)

    if hasattr(user, "discord"):  # Check if the user has a Discord account
        if allianceauth_discordbot_installed():
            logger.debug(
                "Discord bot is installed, messages will be sent via Discord bot."
            )
            _discordbot_send_direct_message(
                user_id=int(user.discord.uid),
                title=title,
                message=message,
                embed_message=embed_message,
                level=level,
            )
            return
        if not discordnotify_installed():
            if discordproxy_installed():
                logger.debug(
                    "Discord proxy is installed, messages will be sent via Discord proxy."
                )
                _discordproxy_send_direct_message(
                    user_id=int(user.discord.uid),
                    title=title,
                    message=message,
                    embed_message=embed_message,
                    level=level,
                )
            return
        logger.debug("No message sender found, sending of Discord message canceled.")
    else:
        logger.debug(
            "User %s does not have a Discord account, sending of Discord message canceled.",
            user.username,
        )


@shared_task
def send_webhook_notification(
    webhook_url: str,
    title: str,
    message: str,
    embed_message: bool = True,
    level: str = "info",
) -> None:
    """Send a notification as a Celery Task to a webhook."""
    if webhook_url is None:
        logger.debug("No webhook URL given. Webhook notification not sent.")
        return

    # Send the message to the webhook using the appropriate method
    notification_sent = _discordwebhook_send_message(
        webhook_url=webhook_url,
        title=title,
        message=message,
        embed_message=embed_message,
        level=level,
    )

    # If sending failed (`False`), retry with a delay and a maximum of 3 retries.
    # `None` means not sent and a retry cannot help, so it is not retried.
    if notification_sent is False:
        logger.warning(
            "Failed to send webhook notification. Check the webhook URL and try again."
        )
        try:
            send_webhook_notification.retry(
                args=[webhook_url, title, message, embed_message, level],
                countdown=2,  # Delay in seconds before retrying
                max_retries=3,
            )
        except MaxRetriesExceededError:
            # The exception text contains the task arguments and with them the
            # webhook URL with the token, so the exception is not raised.
            logger.warning(
                "Failed to send webhook notification after the maximum number of retries."
            )
