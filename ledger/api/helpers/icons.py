# Django
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.api.schema import LedgerRequestInfo
from ledger.models.planetary import CharacterPlanetDetails
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


def get_factory_info_button(
    planet_details: CharacterPlanetDetails,
) -> str:
    """
    Generate a Factory Info button for the Planetary View.

    This function creates a HTML info button for viewing a Factory from an Planet.
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

    This function creates a HTML info button for viewing a Extractor from an Planet.
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

    This function creates a HTML toggle button for Toggle Notification from an Planet.
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
    request_info: LedgerRequestInfo,
    section: str = "summary",
) -> str:
    """
    Generate a Character Details Info button for the Character Ledger View.

    This function creates a HTML info button for viewing a detailed ledger from Owner.
    When clicked, it triggers a modal to display detailed information about the Owner.

    Args:
        character_id (int): The character ID to be viewed.
        request_info (LedgerRequestInfo): The request information containing date and section details.
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


def get_character_details_popover_button(
    ref_types: list[str],
) -> str:
    """
    Generate a Character Details Popover button for the Character Ledger View.

    This function creates a HTML popover button for viewing a detailed ledger from Owner.
    When clicked, it triggers a popover to display detailed information about the Owner.

    Args:
        character_id (int): The character ID to be viewed.
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
