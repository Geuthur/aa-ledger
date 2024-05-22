from django.template.defaulttags import register


@register.filter(name="ledger_init")
def ledger_init():
    return None
