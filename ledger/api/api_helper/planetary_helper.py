# Django
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.evelinks.eveimageserver import (
    type_render_url,
)


def get_facilities_info(planet):
    facilities = []
    for __, facility_info in planet.facilitys.items():
        resources = facility_info["resources"]
        resource_counts = get_resource_counts(resources)

        input_icons = [
            {
                "icon_url": resource["item_id"],
                "item_name": resource["item_name"],
                "count": resource["count"],
            }
            for resource in resource_counts.values()
        ]

        output_icon = (
            {
                "icon_url": facility_info["output_product"]["item_id"],
                "item_name": facility_info["output_product"]["item_name"],
            }
            if facility_info["output_product"]
            else None
        )

        producing = any(resource["still_producing"] for resource in resources)
        is_active = not any(resource["missing_quantity"] > 0 for resource in resources)
        if producing and any(
            resource["missing_quantity"] > 0 for resource in resources
        ):
            is_active = True

        facilities.append(
            {
                "facility_name": facility_info["facility_name"] or _("No facility"),
                "input_icons": input_icons,
                "output_icon": output_icon,
                "is_active": is_active,
            }
        )
    return facilities


def get_resource_counts(resources):
    resource_counts = {}
    for resource in resources:
        if resource["item_id"] not in resource_counts:
            resource_counts[resource["item_id"]] = {
                "item_id": resource["item_id"],
                "item_name": resource["item_name"],
                "count": 0,
            }
        resource_counts[resource["item_id"]]["count"] += 1
    return resource_counts


def generate_progressbar(percentage: float) -> str:
    """
    Generate a progress bar based on the percentage.
    """
    percentage = round(percentage, 2)

    if percentage > 50:
        progress_value = format_html('<span class="text-white)">{}%</span>', percentage)
    else:
        progress_value = format_html('<span class="text-dark">{}%</span>', percentage)

    progressbar = format_html(
        """
        <div class="progress-outer flex-grow-1 me-2">
            <div class="progress" style="position: relative;">
                <div class="progress-bar progress-bar-warning progress-bar-striped active" role="progressbar" style="width: {}%; box-shadow: -1px 3px 5px rgba(0, 180, 231, 0.9);"></div>
                <div class="fw-bold fs-6 text-center position-absolute top-50 start-50 translate-middle">{}</div>
            </div>
        </div>
        """,
        percentage,
        progress_value,
    )

    return progressbar


def get_type_render_url(
    type_id: int, size: int = 32, type_name: str = None, as_html: bool = False
) -> str:
    """Get the type render for a type ID."""

    render_url = type_render_url(type_id=type_id, size=size)

    if as_html:
        render_html = format_html(
            '<img class="type-render rounded-circle" src="{}" title="{}">',
            render_url,
            type_name,
        )
        return render_html
    return render_url
