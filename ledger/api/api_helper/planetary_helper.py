# Third Party
from ninja import schema

# Django
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.evelinks.eveimageserver import (
    character_portrait_url,
    type_icon_url,
    type_render_url,
)
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveType

# AA Ledger
from ledger import __title__
from ledger.models.planetary import CharacterPlanetDetails

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class ProductSchema(schema.Schema):
    item_id: int
    item_name: str
    item_quantity: int | None = None
    icon: str | None = None


class FactorySchema(schema.Schema):
    factory_name: str
    products: list[ProductSchema]
    is_active: str


class ProduceSchema(schema.Schema):
    factory_name: str
    input_products: list[ProductSchema]
    output_product: ProductSchema | None = None
    is_active: str


class StorageSchema(schema.Schema):
    factory_name: str
    product: ProductSchema


def get_factories_info(planet_details: CharacterPlanetDetails) -> list[FactorySchema]:
    """
    Get the factories information for a planet.

    Args:
        planet_details (CharacterPlanetDetails): The planetary details object.
    Returns:
        list[FactorySchema]: A list with the factory information for the Planet.
    """
    response_factories_list: list[FactorySchema] = []

    try:
        factories = planet_details.factories.values()
    except AttributeError:
        return response_factories_list

    for factory_info in factories:
        factory_name = factory_info.get("facility_name") or _("No facility")
        # Only process Processors
        if factory_info.get("facility_type") != "Processors":
            continue

        ressource_types = get_resource_type(factory_info["ressources"])
        ressource_list = []

        # Build Ressource List from Factories
        for product in ressource_types.values():
            product = ProductSchema(
                item_id=product["item_id"],
                item_name=product["item_name"],
                icon=get_icon_render_url(
                    type_id=product["item_id"],
                    type_name=product["item_name"],
                    as_html=True,
                ),
            )
            ressource_list.append(product)

        # Populate Product if exists
        if factory_info.get("output_product", None) is not None:
            output_product = ProductSchema(
                item_id=factory_info["output_product"]["item_id"],
                item_name=factory_info["output_product"]["item_name"],
                icon=get_icon_render_url(
                    type_id=factory_info["output_product"]["item_id"],
                    type_name=factory_info["output_product"]["item_name"],
                    as_html=True,
                ),
            )
            ressource_list.append(output_product)

        is_active = factory_info.get("is_active", False)

        response_factories_list.append(
            FactorySchema(
                factory_name=factory_name,
                products=ressource_list,
                is_active=generate_is_active_icon(is_active),
            )
        )
    return response_factories_list


def get_factory_info(planet_details: CharacterPlanetDetails) -> list[FactorySchema]:
    """
    Get the factory information for a planet.

    Args:
        planet_details (CharacterPlanetDetails): The planetary details object.
    Returns:
        list[FactorySchema]: A list with the factory information for the Planet.
    """
    response_factories_list: list[FactorySchema] = []

    try:
        factories = planet_details.factories.values()
    except AttributeError:
        return response_factories_list

    for factory_info in factories:
        factory_name = factory_info.get("facility_name") or _("No facility")
        # Only process Processors
        if factory_info.get("facility_type") != "Processors":
            continue

        ressource_types = get_resource_type(factory_info["ressources"])
        input_products_list = []

        # Build Ressource List from Factories
        for input_ressource in ressource_types.values():
            input_ressource = ProductSchema(
                item_id=input_ressource["item_id"],
                item_name=input_ressource["item_name"],
                icon=get_icon_render_url(
                    type_id=input_ressource["item_id"],
                    type_name=input_ressource["item_name"],
                    as_html=True,
                ),
            )
            input_products_list.append(input_ressource)

        output_product = None
        # Get Output Product if exists
        if factory_info.get("output_product", None) is not None:
            output_product = ProductSchema(
                item_id=factory_info["output_product"]["item_id"],
                item_name=factory_info["output_product"]["item_name"],
                icon=get_icon_render_url(
                    type_id=factory_info["output_product"]["item_id"],
                    type_name=factory_info["output_product"]["item_name"],
                    as_html=True,
                ),
            )

        is_active = factory_info.get("is_active", False)

        response_factories_list.append(
            ProduceSchema(
                factory_name=factory_name,
                input_products=input_products_list,
                output_product=output_product,
                is_active=generate_is_active_icon(is_active),
            )
        )
    return response_factories_list


def get_storage_info(planet_details: CharacterPlanetDetails) -> list[StorageSchema]:
    """
    Get the storage information for a planet.

    Args:
        planet_details (CharacterPlanetDetails): The planetary details object.
    Returns:
        list[StorageSchema]: A list with the storage information for the Planet.
    """
    response_storage_list: list[StorageSchema] = []

    try:
        factories = planet_details.factories.values()
    except AttributeError:
        return response_storage_list

    for factory in factories:
        factory_name = factory.get("facility_name") or _("No facility")

        # Storage Info
        storage = factory.get("storage", {}) or {}
        for type_id, stored in storage.items():
            # Get Eve Type
            type_data = EveType.objects.get_or_create_esi(id=type_id)[0]

            # Get Amount if Available
            amount = (
                stored.get("amount")
                or stored.get("quantity")
                or stored.get("item_quantity")
                or stored.get("stored")
                or 0
            )

            # Store Storage Information
            response_storage_list.append(
                StorageSchema(
                    factory_name=factory_name,
                    product=ProductSchema(
                        item_id=type_id,
                        item_name=type_data.name,
                        item_quantity=int(amount) if amount is not None else None,
                        icon=get_icon_render_url(
                            type_id=type_id, type_name=type_data.name, as_html=True
                        ),
                    ),
                )
            )
    return response_storage_list


def generate_is_active_icon(is_active: bool) -> str:
    """
    Generate an HTML icon representing the active status.

    Args:
        is_active (bool): The active status.
    Returns:
        str: HTML string representing the active status icon.
    """
    color = "danger"
    if is_active:
        color = "success"
    return format_html(
        '<span class="fs-5 text-{}" data-bs-tooltip="aa-ledger" title="{}">⬤</span>',
        color,
        _("Active" if is_active else "Inactive"),
    )


def generate_is_notification_icon(is_notification: bool) -> str:
    """
    Generate an HTML icon representing the notification status.

    Args:
        is_notification (bool): The notification status.
    Returns:
        str: HTML string representing the notification status icon.
    """
    color = "danger"
    if is_notification:
        color = "success"
    return format_html(
        '<i class="fa-solid fa-bullhorn text-{}" style="margin-left: 5px;" data-bs-tooltip="aa-ledger" title="{}"></i>',
        color,
        _("Active" if is_notification else "Inactive"),
    )


def get_resource_type(ressources):
    """
    Get the resource types.

    Args:
        ressources (list): List of resource dictionaries.
    Returns:
        dict: Dictionary of unique resource types.
    """
    resource_types = {}
    for ressource in ressources:
        # Create a new entry if item_id not in resource_types
        if ressource["item_id"] not in resource_types:
            resource_types[ressource["item_id"]] = {
                "item_id": ressource["item_id"],
                "item_name": ressource["item_name"],
            }
    return resource_types


def allocate_overall_progress(planet_details: CharacterPlanetDetails) -> float | None:
    """
    Calculate the overall progress percentage of all extractors on the planet.

    Args:
        planet_details (CharacterPlanetDetails): The planetary details object.
    Returns:
        float | None: The overall progress percentage, or None if no extractors are present.
    """
    progress_sum = 0.0
    valid_extractors = 0

    try:
        factories = planet_details.factories.values()
    except AttributeError:
        return None

    for factory in factories:
        extractor = factory.get("extractor", {})

        # Skip if no extractor present
        if not extractor:
            continue

        # Get Progress from Extractors
        progress = extractor.get("progress_percentage")
        if progress is not None:
            progress_sum += float(progress)
            valid_extractors += 1
            continue

    if valid_extractors == 0:
        return None

    return round(progress_sum / valid_extractors, 2)


def generate_progressbar(percentage: float | None) -> str:
    """
    Generate a progress bar based on the percentage.

    This function creates an HTML representation of a progress bar
    with a colored percentage display.

    Args:
        percentage (float): The percentage to display in the progress bar.
    Returns:
        str: HTML string representing the progress bar.
    """
    if percentage is None:
        return str(_("No active extractors"))

    if percentage > 50:
        progress_value = f'<span class="text-white)">{percentage}%</span>'
    else:
        progress_value = f'<span class="text-dark">{percentage}%</span>'

    progressbar = f"""
        <div class="progress-outer flex-grow-1 me-2">
            <div class="progress" style="position: relative;">
                <div class="progress-bar progress-bar-warning progress-bar-striped active" role="progressbar" style="width: {percentage}%; box-shadow: -1px 3px 5px rgba(0, 180, 231, 0.9);"></div>
                <div class="fw-bold fs-6 text-center position-absolute top-50 start-50 translate-middle">{progress_value}</div>
            </div>
        </div>
    """
    return progressbar


def get_character_render_url(
    character_id: int, size: int = 32, character_name: str = None, as_html: bool = False
) -> str:
    """Get the character render for a character ID."""

    render_url = character_portrait_url(character_id=character_id, size=size)

    if as_html:
        render_html = format_html(
            '<img class="type-render rounded-circle" data-bs-tooltip="aa-ledger" src="{}" title="{}">',
            render_url,
            character_name,
        )
        return render_html
    return render_url


def get_type_render_url(
    type_id: int, size: int = 32, type_name: str = None, as_html: bool = False
) -> str:
    """Get the type render for a type ID."""

    render_url = type_render_url(type_id=type_id, size=size)

    if as_html:
        render_html = format_html(
            '<img class="type-render rounded-circle" data-bs-tooltip="aa-ledger" src="{}" title="{}">',
            render_url,
            type_name,
        )
        return render_html
    return render_url


def get_icon_render_url(
    type_id: int, size: int = 32, type_name: str = None, as_html: bool = False
) -> str:
    """Get the icon render for a type ID."""

    render_url = type_icon_url(type_id=type_id, size=size)

    if as_html:
        render_html = format_html(
            '<img class="type-render rounded-circle" data-bs-tooltip="aa-ledger" src="{}" title="{}">',
            render_url,
            type_name,
        )
        return render_html
    return render_url
