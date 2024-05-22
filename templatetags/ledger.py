from django import template
from django.template.defaulttags import register

from datetime import datetime

register = template.Library()

@register.filter(name='format_currency')
def format_currency(value):
    try:
        value = '{:,.0f}'.format(value).replace(',', '.')
    except:
        value = 0
    return value

@register.filter(name='current_month')
def current_month(value):
    return datetime.now().strftime("%B")

@register.filter(name='current_year')
def current_year(value):
    return datetime.now().strftime("%Y")

@register.filter(name='portrait')
def portrait(character_id):
    portrait = f"https://images.evetech.net/characters/{character_id}/portrait?size=32"
    return portrait