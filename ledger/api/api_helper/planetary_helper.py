from django.utils.translation import gettext as trans


def get_facilities_info(planet):
    facilities = []
    for _, facility_info in planet.facilitys.items():
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
                "facility_name": facility_info["facility_name"] or trans("No facility"),
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
