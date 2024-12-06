from django.db import models

from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class PlanetaryQuerySet(models.QuerySet):
    pass


class PlanetaryManagerBase(models.Manager):
    pass


PlanetaryManager = PlanetaryManagerBase.from_queryset(PlanetaryQuerySet)
