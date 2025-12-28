"""This module provides helper functions to get EVE Online related images and renders."""

# Django
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.evelinks.eveimageserver import (
    alliance_logo_url,
    character_portrait_url,
    corporation_logo_url,
    type_render_url,
)


def get_character_portrait_url(
    character_id: int, size: int = 32, character_name: str = "", as_html: bool = False
) -> str:
    """
    Get the character portrait for a character ID.

    Args:
        character_id (int): The ID of the character.
        size (int, optional): The size of the portrait image.
        character_name (str, optional): The name of the character.
        as_html (bool, optional): Whether to return the portrait as an HTML img tag.
    Returns:
        str: The URL of the character portrait or an HTML img tag.
    """
    try:
        render_url = character_portrait_url(character_id=character_id, size=size)
    except ValueError:
        return ""

    if as_html:
        render_html = format_html(
            '<img class="character-portrait rounded-circle" src="{}" alt="{}">',
            render_url,
            character_name,
        )
        return render_html
    return render_url


def get_corporation_logo_url(
    corporation_id: int,
    size: int = 32,
    corporation_name: str = "",
    as_html: bool = False,
) -> str:
    """
    Get the corporation logo for a corporation ID.

    Args:
        corporation_id (int): The ID of the corporation.
        size (int, optional): The size of the logo image.
        corporation_name (str, optional): The name of the corporation.
        as_html (bool, optional): Whether to return the logo as an HTML img tag.
    Returns:
        str: The URL of the corporation logo or an HTML img tag.
    """

    render_url = corporation_logo_url(corporation_id=corporation_id, size=size)

    if as_html:
        render_html = format_html(
            '<img class="corporation-logo rounded-circle" src="{}" alt="{}">',
            render_url,
            corporation_name,
        )
        return render_html
    return render_url


def get_alliance_logo_url(
    alliance_id: int,
    size: int = 32,
    alliance_name: str = "",
    as_html: bool = False,
) -> str:
    """
    Get the alliance logo for a alliance ID.

    Args:
        alliance_id (int): The ID of the alliance.
        size (int, optional): The size of the logo image.
        alliance_name (str, optional): The name of the alliance.
        as_html (bool, optional): Whether to return the logo as an HTML img tag.

    Returns:
        str: The URL of the alliance logo or an HTML img tag.
    """

    render_url = alliance_logo_url(alliance_id=alliance_id, size=size)

    if as_html:
        render_html = format_html(
            '<img class="alliance-logo rounded-circle" src="{}" alt="{}">',
            render_url,
            alliance_name,
        )
        return render_html
    return render_url


def get_type_render_url(
    type_id: int, size: int = 32, type_name: str = "", as_html: bool = False
) -> str:
    """
    Get the type render for a type ID.

    Args:
        type_id (int): The ID of the type.
        size (int, optional): The size of the render image.
        type_name (str, optional): The name of the type.
        as_html (bool): Whether to return the render as an HTML img tag.

    Returns:
        str: The URL of the type render or an HTML img tag.
    """

    render_url = type_render_url(type_id=type_id, size=size)

    if as_html:
        render_html = format_html(
            '<img class="type-render rounded-circle" src="{}" alt="{}">',
            render_url,
            type_name,
        )
        return render_html
    return render_url
