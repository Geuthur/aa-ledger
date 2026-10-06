# Third Party
from ninja import schema

# Django
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from eve_sde.models.types import ItemType

# AA Ledger
from ledger import __title__
from ledger.helpers.eveonline import get_icon_render_url
from ledger.models.planetary import CharacterPlanetDetails
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class ProductSchema(schema.Schema):
    item_id: int
    item_name: str
    item_quantity: int | None = None
    icon: str | None = None


class ProduceSchema(schema.Schema):
    factory_name: str
    input_products: list[ProductSchema]
    output_product: ProductSchema | None = None
    is_active: bool


class StorageSchema(schema.Schema):
    factory_name: str
    product: ProductSchema


def _product(item_id: int, item_name: str, quantity: int | None = None):
    return ProductSchema(
        item_id=item_id,
        item_name=item_name,
        item_quantity=quantity,
        icon=get_icon_render_url(type_id=item_id, type_name=item_name),
    )


def get_factory_info(planet_details: CharacterPlanetDetails) -> list[ProduceSchema]:
    """
    Get the processor information for a planet.

    Args:
        planet_details (CharacterPlanetDetails): The planetary details object.
    Returns:
        list[ProduceSchema]: Processors with their input and output products.
    """
    response_factories_list: list[ProduceSchema] = []

    try:
        factories = planet_details.factories.values()
    except AttributeError:
        return response_factories_list

    for factory_info in factories:
        # Only process Processors that are running something
        if factory_info.get("facility_type") != "Processors":
            continue
        ressources = factory_info.get("ressources") or None
        if ressources is None:
            continue

        output = factory_info.get("output_product")
        response_factories_list.append(
            ProduceSchema(
                factory_name=factory_info.get("facility_name") or _("No facility"),
                input_products=[
                    _product(item["item_id"], item["item_name"])
                    for item in get_resource_type(ressources).values()
                ],
                output_product=(
                    _product(output["item_id"], output["item_name"])
                    if output is not None
                    else None
                ),
                is_active=bool(factory_info.get("is_active", False)),
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

        storage = factory.get("storage", {}) or {}
        for type_id, stored in storage.items():
            type_data = ItemType.objects.get(id=type_id)

            amount = (
                stored.get("amount")
                or stored.get("quantity")
                or stored.get("item_quantity")
                or stored.get("stored")
                or 0
            )

            response_storage_list.append(
                StorageSchema(
                    factory_name=factory_name,
                    product=_product(int(type_id), type_data.name, int(amount)),
                )
            )
    return response_storage_list


def get_resource_type(ressources):
    """
    Get the unique resource types.

    Args:
        ressources (list): List of resource dictionaries.
    Returns:
        dict: Dictionary of unique resource types.
    """
    resource_types = {}
    for ressource in ressources:
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

        progress = extractor.get("progress_percentage")
        if progress is not None:
            progress_sum += float(progress)
            valid_extractors += 1

    if valid_extractors == 0:
        return None

    return round(progress_sum / valid_extractors, 2)
