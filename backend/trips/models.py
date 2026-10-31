from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from vehicles.models import Vehicle


class Trip(models.Model):
    class Status(models.TextChoices):
     PLANNED = "PLANNED", "Planejada"
     IN_PROGRESS = "IN_PROGESS", "Em andamento"
     COMPLETED = "COMPLETO," "finalizada"
     CANCELLED = "CANCELLED", "Cancelada"