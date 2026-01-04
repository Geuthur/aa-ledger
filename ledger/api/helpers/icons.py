# Django
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.api.schema import CorporationLedgerRequestInfo, OwnerLedgerRequestInfo
from ledger.helpers.eveonline import get_character_portrait_url
from ledger.models.planetary import CharacterPlanetDetails
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


def get_factory_info_button(
    planet_details: CharacterPlanetDetails,
) -> str:
    """
    Generate a Factory Info button for the Planetary View.

    When clicked, it triggers a modal to display detailed information about the Factory.

    Args:
        planet_details (CharacterPlanetDetails): The planetary details object to be viewed.
    Returns:
        String: HTML string containing the info button.
    """

    # Generate the URL for the delete Request
    button_request_info_url = reverse(
        "ledger:api:get_factory_details",
        kwargs={
            "character_id": planet_details.character.eve_character.character_id,
            "planet_id": planet_details.planet.id,
        },
    )

    # Define the icon and tooltip for the delete button
    icon = '<i class="fa-solid fa-info"></i>'
    title = _("View Factory")
    color = "primary"

    # Create the HTML for the delete icon button
    factory_info_button = (
        f'<button data-action="{button_request_info_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-ledger" '
        'data-bs-target="#ledger-view-planetary-factory" '
        f'title="{title}">{icon}</button>'
    )
    return factory_info_button


def get_extractor_info_button(
    planet_details: CharacterPlanetDetails,
) -> str:
    """
    Generate a Extractor Info button for the Planetary View.

    When clicked, it triggers a modal to display detailed information about the Extractor.

    Args:
        planet_details (CharacterPlanetDetails): The planetary details object to be viewed.
    Returns:
        String: HTML string containing the info button.
    """

    # Generate the URL for the delete Request
    button_request_info_url = reverse(
        "ledger:api:get_extractor_details",
        kwargs={
            "character_id": planet_details.character.eve_character.character_id,
            "planet_id": planet_details.planet.id,
        },
    )

    # Define the icon and tooltip for the delete button
    icon = '<i class="fa-solid fa-info"></i>'
    title = _("View Extractor")
    color = "primary"

    # Create the HTML for the delete icon button
    extractor_info_button = (
        f'<button data-action="{button_request_info_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-ledger" '
        'data-bs-target="#ledger-view-planetary-extractor" '
        f'title="{title}">{icon}</button>'
    )
    return extractor_info_button


def get_toggle_notification_button(
    planet_details: CharacterPlanetDetails,
) -> str:
    """
    Generate a Notification Toggle button for the Planetary View.

    When clicked, it triggers a modal to confirm the action.

    Args:
        planet_details (CharacterPlanetDetails): The planetary details object to be viewed.
    Returns:
        String: HTML string containing the info button.
    """

    # Generate the URL for the delete Request
    button_request_info_url = reverse(
        "ledger:api:toggle_planet_notification",
        kwargs={
            "character_id": planet_details.character.eve_character.character_id,
            "planet_id": planet_details.planet.id,
        },
    )

    # Define the icon and tooltip for the delete button
    icon = '<i class="fa-solid fa-bullhorn"></i>'
    title = _("Toggle Notification")
    color = "primary"

    # Create the HTML for the delete icon button
    notification_toggle_button = (
        f'<button data-action="{button_request_info_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-ledger" '
        'data-bs-target="#ledger-accept-planet-toggle-notification" '
        f'title="{title}">{icon}</button>'
    )
    return notification_toggle_button


def get_character_details_info_button(
    character_id: int,
    request_info: OwnerLedgerRequestInfo,
    section: str = "summary",
) -> str:
    """
    Generate a Character Details Info button for the Character Ledger View.

    When clicked, it triggers a modal to display detailed information about the Character.

    Args:
        character_id (int): The character ID to be viewed.
        request_info (LedgerRequestInfo): The request information containing date and section details.
        section (str): The section of the ledger to view.
    Returns:
        String: HTML string containing the info button.
    """

    kwargs = {"character_id": character_id, "section": section}
    if request_info.year is not None:
        kwargs["year"] = request_info.year
    if request_info.month is not None:
        kwargs["month"] = request_info.month
    if request_info.day is not None:
        kwargs["day"] = request_info.day

    # Generate the URL for the Info Request
    button_request_info_url = reverse(
        "ledger:api:get_character_ledger_details", kwargs=kwargs
    )

    # Define the icon and tooltip for the Info button
    icon = '<i class="fa-solid fa-info"></i>'
    title = _("View Details")
    color = "primary"

    # Create the HTML for the Info icon button
    ledger_info_button = (
        f'<button data-action="{button_request_info_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-ledger" '
        'data-bs-target="#ledger-view-character-ledger-details" '
        f'title="{title}">{icon}</button>'
    )
    return ledger_info_button


def get_ref_type_details_popover_button(
    ref_types: list[str],
) -> str:
    """
    Generate a Character Details Popover button for the Character Ledger View.

    When hover, it triggers a popover to display information about the Ref Types.

    Args:
        ref_types (list[str]): The list of reference types to be viewed.
    Returns:
        String: HTML string containing the popover button.
    """

    # Define the icon and tooltip for the Ref Type button
    icon = '<i class="fa-solid fa-info-circle"></i>'
    title = _("Included Reference Types")
    color = "primary"

    # Create the HTML for the popover icon button
    ledger_popover_button = (
        f"<button "
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="popover" '
        'data-bs-popover="aa-ledger" '
        'data-bs-trigger="hover" '
        'data-bs-placement="top" '
        'data-bs-html="true" '
        f'data-bs-content="{", ".join(ref_types)}" '
        f'title="{title}">{icon}</button>'
    )
    return ledger_popover_button


def get_corporation_ledger_popover_button(
    alts: models.QuerySet[CharacterOwnership],
) -> str:
    """
    Generate a Corporation Ledger Popover button for the Corporation Ledger View.

    When hover, it triggers a popover to display information about all Alt characters from the Account.

    Args:
        alts (models.QuerySet[CharacterOwnership]): The queryset of alt characters to be viewed.
    Returns:
        String: HTML string containing the popover button.
    """
    if not alts:
        return ""

    # Define the icon and tooltip for the Ref Type button
    title = _("Included Alt Characters")

    pieces: list[str] = []
    for alt in alts:
        portrait = get_character_portrait_url(
            character_id=alt.character.character_id,
            character_name=alt.character.character_name,
            size=32,
            as_html=True,
        )
        pieces.append(f"{portrait} {alt.character.character_name}<br>")

    # join HTML, escape double-quotes for safe attribute embedding
    content_html = "".join(pieces).replace('"', "&quot;")

    ledger_popover_icon = (
        f'<i class="fa-solid fa-circle-question" '
        f'data-bs-toggle="popover" '
        'data-bs-popover="aa-ledger" '
        'data-bs-trigger="hover" '
        'data-bs-placement="top" '
        'data-bs-html="true" '
        f'data-bs-content="{content_html}" '
        f'title="{title}"></i>'
    )
    return ledger_popover_icon


def get_corporation_details_info_button(
    entity_id: int,
    request_info: CorporationLedgerRequestInfo,
    section: str = "summary",
) -> str:
    """
    Generate a Entity Details Info button for the Corporation Ledger View.

    When clicked, it triggers a modal to display detailed information about the Entity.

    Args:
        corporation_id (int): The corporation ID to be viewed.
        entity_id (int): The entity ID to be viewed.
        section (str): The section of the ledger to view.
        request_info (CorporationLedgerRequestInfo): The request information containing date and section details.
    Returns:
        String: HTML string containing the info button.
    """

    kwargs = {
        "corporation_id": request_info.owner_id,
        "entity_id": entity_id,
        "section": section,
    }
    if request_info.year is not None:
        kwargs["year"] = request_info.year
    if request_info.month is not None:
        kwargs["month"] = request_info.month
    if request_info.day is not None:
        kwargs["day"] = request_info.day

    # Generate the URL for the Info Request
    button_request_info_url = reverse(
        "ledger:api:get_corporation_ledger_details", kwargs=kwargs
    )

    # Define the icon and tooltip for the Info button
    icon = '<i class="fa-solid fa-info"></i>'
    title = _("View Details")
    color = "primary"

    # Create the HTML for the Info icon button
    ledger_info_button = (
        f'<button data-action="{button_request_info_url}" '
        f'class="btn btn-{color} btn-sm btn-square me-2" '
        'data-bs-toggle="modal" '
        'data-bs-tooltip="aa-ledger" '
        'data-bs-target="#ledger-view-corporation-ledger-details" '
        f'title="{title}">{icon}</button>'
    )
    return ledger_info_button
