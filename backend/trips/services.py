import logging
from uuid import uuid4

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import User
from vehicles.models import Vehicle
from .models import Trip


logger = logging.getLogger(__name__)


def start_trip(*, trip_id, actor_id, start_km, photo):
    uploaded_photo = None

    try:
        with transaction.atomic():
            trip = Trip.objects.select_for_update().get(pk=trip_id)

            driver = User.objects.select_for_update().get(
                pk=trip.driver_id
            )

            vehicle = Vehicle.objects.select_for_update().get(
                pk=trip.vehicle_id
            )

            if (
                driver.pk != actor_id
                or not driver.is_active
                or driver.role != User.Role.DRIVER
            ):
                raise PermissionDenied(
                    "Somente o motorista responsável pode iniciar a viagem."
                )

            if trip.status != Trip.Status.PLANNED:
                raise ValidationError(
                    {
                        "status": (
                            "Somente viagens planejadas podem ser iniciadas."
                        )
                    }
                )

            if vehicle.status != Vehicle.Status.ACTIVE:
                raise ValidationError(
                    {"vehicle": "O veículo não está ativo."}
                )

            if start_km < vehicle.current_km:
                raise ValidationError(
                    {
                        "start_km": (
                            "A quilometragem inicial não pode ser menor "
                            "que a quilometragem atual do veículo."
                        )
                    }
                )

            active_trips = Trip.objects.filter(
                status=Trip.Status.IN_PROGRESS
            ).exclude(pk=trip.pk)

            if active_trips.filter(driver_id=driver.pk).exists():
                raise ValidationError(
                    {
                        "driver": (
                            "O motorista já possui uma viagem em andamento."
                        )
                    }
                )

            if active_trips.filter(vehicle_id=vehicle.pk).exists():
                raise ValidationError(
                    {
                        "vehicle": (
                            "O veículo já possui uma viagem em andamento."
                        )
                    }
                )

            extension = {
                "JPEG": "jpg",
                "PNG": "png",
            }[photo.image.format]

            photo.name = f"{uuid4().hex}.{extension}"

            trip.driver = driver
            trip.vehicle = vehicle
            trip.start_km = start_km
            trip.start_odometer_photo = photo
            trip.started_at = timezone.now()
            trip.status = Trip.Status.IN_PROGRESS

            uploaded_photo = trip.start_odometer_photo

            try:
                trip.full_clean()
            except DjangoValidationError as exc:
                if hasattr(exc, "message_dict"):
                    raise ValidationError(exc.message_dict) from exc

                raise ValidationError(
                    {"detail": exc.messages}
                ) from exc

            trip.save(
                update_fields=[
                    "start_km",
                    "start_odometer_photo",
                    "started_at",
                    "status",
                    "updated_at",
                ]
            )

        return trip

    except Exception:
        if uploaded_photo is not None and uploaded_photo._committed:
            try:
                uploaded_photo.storage.delete(uploaded_photo.name)
            except Exception:
                logger.exception(
                    "Não foi possível remover a foto após falha no início."
                )

        raise


def finish_trip(*, trip_id, actor_id, end_km, photo):
    uploaded_photo = None

    try:
        with transaction.atomic():
            trip = Trip.objects.select_for_update().get(pk=trip_id)

            driver = User.objects.select_for_update().get(
                pk=trip.driver_id
            )

            vehicle = Vehicle.objects.select_for_update().get(
                pk=trip.vehicle_id
            )

            if (
                driver.pk != actor_id
                or not driver.is_active
                or driver.role != User.Role.DRIVER
            ):
                raise PermissionDenied(
                    "Somente o motorista responsável pode finalizar a viagem."
                )

            if trip.status != Trip.Status.IN_PROGRESS:
                raise ValidationError(
                    {
                        "status": (
                            "Somente viagens em andamento podem ser finalizadas."
                        )
                    }
                )

            if trip.start_km is None:
                raise ValidationError(
                    {
                        "start_km": (
                            "A viagem não possui quilometragem inicial."
                        )
                    }
                )

            if end_km < trip.start_km:
                raise ValidationError(
                    {
                        "end_km": (
                            "A quilometragem final não pode ser menor "
                            "que a quilometragem inicial."
                        )
                    }
                )

            if end_km < vehicle.current_km:
                raise ValidationError(
                    {
                        "end_km": (
                            "A quilometragem final não pode ser menor "
                            "que a quilometragem atual do veículo."
                        )
                    }
                )

            extension = {
                "JPEG": "jpg",
                "PNG": "png",
            }[photo.image.format]

            photo.name = f"{uuid4().hex}.{extension}"

            trip.driver = driver
            trip.vehicle = vehicle
            trip.end_km = end_km
            trip.end_odometer_photo = photo
            trip.ended_at = timezone.now()
            trip.status = Trip.Status.COMPLETED

            uploaded_photo = trip.end_odometer_photo

            try:
                trip.full_clean()
            except DjangoValidationError as exc:
                if hasattr(exc, "message_dict"):
                    raise ValidationError(exc.message_dict) from exc

                raise ValidationError(
                    {"detail": exc.messages}
                ) from exc

            trip.save(
                update_fields=[
                    "end_km",
                    "end_odometer_photo",
                    "ended_at",
                    "status",
                    "updated_at",
                ]
            )

            vehicle.current_km = end_km

            vehicle.save(
                update_fields=[
                    "current_km",
                    "updated_at",
                ]
            )

        return trip

    except Exception:
        if uploaded_photo is not None and uploaded_photo._committed:
            try:
                uploaded_photo.storage.delete(uploaded_photo.name)
            except Exception:
                logger.exception(
                    "Não foi possível remover a foto após falha na finalização."
                )

        raise