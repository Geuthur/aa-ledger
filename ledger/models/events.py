"""
Events Model
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Events(models.Model):
    """Event Tracker for Voices of War."""

    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=100, null=True)
    date_start = models.DateTimeField(null=True, blank=True)
    date_end = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    char_ledger = models.BooleanField(null=True, default=False)
    location = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = _("event")
        verbose_name_plural = _("events")
        default_permissions = ()
        permissions = (
            (
                "event_admin_access",
                "Can access Events Tools",
            ),
        )

    def __str__(self):
        return f"Event {self.id}"
