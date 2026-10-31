from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class Vehicle(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Ativo"
        MAINTENANCE = "MAINTENANCE", "Em manutenção"
        INACTIVE = "INACTIVE", "Inativo"

    plate = models.CharField(
        "Placa",
        max_length=7,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$",
                message="Informe uma placa brasileira como ABC1234 ou ABC1D23.",
            )
        ],
    )

    brand = models.CharField("Marca", max_length=50)
    model = models.CharField("Modelo", max_length=80)

    year = models.PositiveSmallIntegerField(
        "Ano",
        validators=[MinValueValidator(1886)],
    )

    color = models.CharField("Cor", max_length=30, blank=True)

    current_km = models.PositiveBigIntegerField(
        "Quilometragem atual",
        default=0,
    )

    status = models.CharField(
        "Situação",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(
        "Criado em",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "Atualizado em",
        auto_now=True,
    )

    class Meta:
        ordering = ["plate"]
        verbose_name = "Veículo"
        verbose_name_plural = "Veículos"

    def __str__(self):
        return f"{self.plate} - {self.brand} {self.model}"