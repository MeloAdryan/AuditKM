from datetime import timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import User
from .models import Trip, TripLocation


def register_trip_location(*, trip_id, actor_id, data):
    payload = {
        "point_id": data["point_id"],
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "accuracy_m": data.get("accuracy_m"),
        "recorded_at": data["recorded_at"],
    }

    with transaction.atomic():
        trip = Trip.objects.select_for_update().get(pk=trip_id)

        driver = User.objects.select_for_update().get(
            pk=trip.driver_id
        )

        if (
            driver.pk != actor_id
            or not driver.is_active
            or driver.role != User.Role.DRIVER
        ):
            raise PermissionDenied(
                "Somente o motorista responsável pode enviar pontos GPS."
            )

        existing = TripLocation.objects.filter(
            trip=trip,
            point_id=payload["point_id"],
        ).first()

        if existing is not None:
            same_data = all(
                getattr(existing, field) == value
                for field, value in payload.items()
            )

            if not same_data:
                raise ValidationError(
                    {
                        "point_id": (
                            "Este identificador já foi usado "
                            "para um ponto com dados diferentes."
                        )
                    }
                )

            return existing, False

        if trip.status not in {
            Trip.Status.IN_PROGRESS,
            Trip.Status.COMPLETED,
        }:
            raise ValidationError(
                {"trip": "Esta viagem não permite receber pontos GPS."}
            )

        if trip.started_at is None:
            raise ValidationError(
                {"trip": "A viagem não possui horário de início."}
            )

        recorded_at = payload["recorded_at"]

        if recorded_at < trip.started_at:
            raise ValidationError(
                {
                    "recorded_at": (
                        "O ponto não pode ter sido capturado "
                        "antes do início da viagem."
                    )
                }
            )

        if recorded_at > timezone.now() + timedelta(seconds=30):
            raise ValidationError(
                {
                    "recorded_at": (
                        "O horário do ponto está no futuro. "
                        "Confira o relógio do dispositivo."
                    )
                }
            )

        if trip.status == Trip.Status.COMPLETED:
            if trip.ended_at is None:
                raise ValidationError(
                    {"trip": "A viagem não possui horário de finalização."}
                )

            if recorded_at > trip.ended_at:
                raise ValidationError(
                    {
                        "recorded_at": (
                            "O ponto não pode ter sido capturado "
                            "depois da finalização da viagem."
                        )
                    }
                )

        location = TripLocation(
            trip=trip,
            **payload,
        )

        try:
            location.full_clean()
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise ValidationError(exc.message_dict) from exc

            raise ValidationError(
                {"detail": exc.messages}
            ) from exc

        location.save()

        return location, True