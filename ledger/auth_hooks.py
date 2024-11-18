"""Hook into Alliance Auth"""

# Django
# Alliance Auth
from django.utils.translation import gettext_lazy as _

from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

from ledger import app_settings, urls


class LedgerMenuItem(MenuItemHook):
    """This class ensures only authorized users will see the menu entry"""

    def __init__(self):
        super().__init__(
            f"{app_settings.LEDGER_APP_NAME}",
            "fas fa-book fa-fw",
            "ledger:ledger_index",
            navactive=["ledger:"],
        )

    def render(self, request):
        if request.user.has_perm("ledger.basic_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_menu():
    """Register the menu item"""

    return LedgerMenuItem()


@hooks.register("url_hook")
def register_urls():
    """Register app urls"""

    return UrlHook(urls, "ledger", r"^ledger/")


@hooks.register("charlink")
def register_charlink_hook():
    return "ledger.thirdparty.charlink_hook"
