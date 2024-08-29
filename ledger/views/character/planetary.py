"""
Planetary Audit
"""

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from ledger.hooks import get_extension_logger
from ledger.view_helpers.core import add_info_to_context

logger = get_extension_logger(__name__)


@login_required
@permission_required(["ledger.admin_access"])
def planetary_index(request):
    context = {}
    context = add_info_to_context(request, context)
    return render(request, "ledger/planetary/index.html", context=context)
