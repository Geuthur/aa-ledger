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

    kwargs = {"character_id": character_id, "section": request_info.section}
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


def get_character_dropdown_button(
    request_info: LedgerRequestInfo,
):
    """
    Generate a Character Dropdown button for the Character Ledger View.

    This function creates a HTML dropdown button for selecting date filters in the Character Ledger View.

    Args:
        request_info (LedgerRequestInfo): The request information containing date and section details.
    """
    year_label = _("Year")
    month_label = _("Month")
    day_label = _("Day")

    html_parts: list[str] = []

    selected_year = (
        request_info.year
        if getattr(request_info, "year", None) is not None
        else (
            sorted(request_info.available_years, reverse=True)[0]
            if request_info.available_years
            else None
        )
    )
    selected_month = (
        request_info.month
        if getattr(request_info, "month", None) is not None
        else (
            sorted(request_info.available_months)[0]
            if request_info.available_months
            else None
        )
    )

    # Year dropdown
    html_parts.append(
        f'<div class="dropdown px-2">'
        f'<button id="yearDropDownButton" class="btn btn-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">{year_label}</button>'
        f'<ul class="dropdown-menu" id="character-ledger-year-selector">'
    )
    if request_info.available_years:
        for year in sorted(request_info.available_years, reverse=True):
            url = reverse(
                "ledger:character_ledger",
                kwargs={
                    "character_id": request_info.character_id,
                    "section": request_info.section,
                    "year": year,
                },
            )
            href = f'href="{url}"'
            class_name = "dropdown-item"
            if request_info.year == year:
                class_name += " active"
                if request_info.month is None:
                    class_name += " disabled"
            html_parts.append(f'<li><a class="{class_name}" {href}>{year}</a></li>')
    html_parts.append("</ul></div>")

    # Month dropdown
    html_parts.append(
        f'<div class="dropdown px-2">'
        f'<button id="monthDropDownButton" class="btn btn-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">{month_label}</button>'
        f'<ul class="dropdown-menu" id="character-ledger-month-selector">'
    )
    if request_info.available_months:
        for month in sorted(request_info.available_months):
            url = reverse(
                "ledger:character_ledger",
                kwargs={
                    "character_id": request_info.character_id,
                    "section": request_info.section,
                    "year": selected_year,
                    "month": month,
                },
            )
            href = f'href="{url}"'
            class_name = "dropdown-item"
            if request_info.month == month:
                class_name += " active"
                if request_info.day is None:
                    class_name += " disabled"
                href = ""
            html_parts.append(f'<li><a class="{class_name}" {href}>{month}</a></li>')
    html_parts.append("</ul></div>")

    # Day dropdown
    html_parts.append(
        f'<div class="dropdown px-2">'
        f'<button id="dayDropDownButton" class="btn btn-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">{day_label}</button>'
        f'<ul class="dropdown-menu" id="character-ledger-day-selector">'
    )
    if request_info.available_days:
        for day in sorted(request_info.available_days):
            url = reverse(
                "ledger:character_ledger",
                kwargs={
                    "character_id": request_info.character_id,
                    "section": request_info.section,
                    "year": selected_year,
                    "month": selected_month,
                    "day": day,
                },
            )
            href = f'href="{url}"'
            class_name = "dropdown-item"
            if request_info.day == day:
                class_name += " active disabled"
                href = ""
            html_parts.append(f'<li><a class="{class_name}" {href}>{day}</a></li>')
    html_parts.append("</ul></div>")

    return "\n".join(html_parts)
