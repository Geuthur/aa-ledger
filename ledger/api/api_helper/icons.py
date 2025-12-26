# Django
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.models.planetary import CharacterPlanetDetails

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


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
