"""Access to the API: every URL of the API requires `basic_access`."""

# Standard Library
from functools import wraps
from http import HTTPStatus

# Django
from django.http import JsonResponse
from django.utils.translation import gettext as _

# AA Ledger
from ledger.managers.general import GeneralManager


def basic_access_required(view_func):
    """
    Answer 403 unless the user has `basic_access`.

    Basic access is only granted by `basic_access`; higher permissions do not
    include it. `urls.py` puts this decorator around all URLs of the API, so
    no endpoint checks `basic_access` itself and none can opt out.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not GeneralManager.has_basic_access(request.user):
            return JsonResponse(
                {"error": _("Permission Denied")}, status=HTTPStatus.FORBIDDEN
            )
        return view_func(request, *args, **kwargs)

    return _wrapped_view
