"""Discord helper functions"""

# Third Party
from celery import shared_task

# Django
from django.apps import apps
from django.utils import timezone

# Alliance Auth
from allianceauth.authentication.models import User
from allianceauth.notifications import notify
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.constants import DISCORD_EMBED_COLOR_MAP

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


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
