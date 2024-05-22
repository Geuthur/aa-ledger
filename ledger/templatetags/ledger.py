from django.template.defaulttags import register


@register.filter(name="format_currency")
def format_currency(value):
    try:
        value = f"{value:,.0f}".replace(",", ".")
    except ValueError:
        value = 0
    return value


@register.filter(name="portrait")
def portrait(character_id):
    portait_img = (
        f"https://images.evetech.net/characters/{character_id}/portrait?size=32"
    )
    return portait_img
