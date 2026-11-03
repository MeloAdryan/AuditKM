from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from vehicles.models import Vehicle


class Trip(models.Model):
    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planejada"
        IN_PROGRESS = "IN_PROGRESS", "Em andamento"
        COMPLETED = "COMPLETED", "Finalizada"
        CANCELLED = "CANCELLED", "Cancelada"

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="trips",
        verbose_name="Motorista",
        limit_choices_to={
            "role": "DRIVER",
            "is_active": True,
        },
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name="trips",
        verbose_name="Veículo",
    )

    origin = models.CharField(
        "Origem",
        max_length=255,
    )

    destination = models.CharField(
        "Destino",
        max_length=255,
    )

    status = models.CharField(
        "Situação",
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )

    start_km = models.PositiveBigIntegerField(
        "Quilometragem inicial",
        null=True,
        blank=True,
    )

    end_km = models.PositiveBigIntegerField(
        "Quilometragem final",
        null=True,
        blank=True,
    )

    start_odometer_photo = models.ImageField(
        "Foto inicial do hodômetro",
        upload_to="trips/odometer/start/%Y/%m/",
        blank=True,
    )

    end_odometer_photo = models.ImageField(
        "Foto final do hodômetro",
        upload_to="trips/odometer/end/%Y/%m/",
        blank=True,
    )

    started_at = models.DateTimeField(
        "Iniciada em",
        null=True,
        blank=True,
    )

    ended_at = models.DateTimeField(
        "Finalizada em",
        null=True,
        blank=True,
    )

    notes = models.TextField(
        "Observações",
        blank=True,
    )

    created_at = models.DateTimeField(
        "Criada em",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "Atualizada em",
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Viagem"
        verbose_name_plural = "Viagens"

        constraints = [
            models.UniqueConstraint(
                fields=["driver"],
                condition=models.Q(status="IN_PROGRESS"),
                name="one_active_trip_per_driver",
            ),
            models.UniqueConstraint(
                fields=["vehicle"],
                condition=models.Q(status="IN_PROGRESS"),
                name="one_active_trip_per_vehicle",
            ),
        ]

    def clean(self):
        super().clean()

        errors = {}

        if self.driver_id:
            if not self.driver.is_active or self.driver.role != "DRIVER":
                errors["driver"] = "Selecione um motorista ativo."

        if self.start_km is not None and self.end_km is not None:
            if self.end_km < self.start_km:
                errors["end_km"] = (
                    "A quilometragem final não pode ser menor que a inicial."
                )

        if self.started_at is not None and self.ended_at is not None:
            if self.ended_at < self.started_at:
                errors["ended_at"] = (
                    "A finalização não pode ocorrer antes do início."
                )

        if self.status in {
            self.Status.IN_PROGRESS,
            self.Status.COMPLETED,
        }:
            if self.start_km is None:
                errors["start_km"] = "Informe a quilometragem inicial."

            if not self.start_odometer_photo:
                errors["start_odometer_photo"] = (
                    "A foto inicial do hodômetro é obrigatória."
                )

            if self.started_at is None:
                errors["started_at"] = "Informe o horário de início."

        if self.status == self.Status.COMPLETED:
            if self.end_km is None:
                errors["end_km"] = "Informe a quilometragem final."

            if not self.end_odometer_photo:
                errors["end_odometer_photo"] = (
                    "A foto final do hodômetro é obrigatória."
                )

            if self.ended_at is None:
                errors["ended_at"] = "Informe o horário de finalização."

        if errors:
            raise ValidationError(errors)

    @property
    def traveled_km(self):
        if self.start_km is None or self.end_km is None:
            return None

        return self.end_km - self.start_km

    def __str__(self):
        return f"Viagem {self.pk} - {self.origin} → {self.destination}"