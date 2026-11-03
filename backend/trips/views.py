from django.db import IntegrityError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from accounts.models import User
from .models import Trip
from .permissions import TripPermission
from .serializers import (
    TripFinishSerializer,
    TripSerializer,
    TripStartSerializer,
)
from .services import finish_trip, start_trip


class TripViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TripSerializer
    permission_classes = [TripPermission]

    def get_queryset(self):
        user = self.request.user

        queryset = Trip.objects.select_related(
            "driver",
            "vehicle",
        ).order_by("-created_at", "-id")

        if not user.is_authenticated:
            return queryset.none()

        if user.is_superuser:
            return queryset

        if user.role in {
            User.Role.ADMIN,
            User.Role.MANAGER,
        }:
            return queryset

        if user.role == User.Role.DRIVER:
            return queryset.filter(driver=user)

        return queryset.none()

    @action(
        detail=True,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
    )
    def start(self, request, pk=None):
        trip = self.get_object()

        serializer = TripStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            trip = start_trip(
                trip_id=trip.pk,
                actor_id=request.user.pk,
                start_km=serializer.validated_data["start_km"],
                photo=serializer.validated_data["start_odometer_photo"],
            )
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "Não foi possível iniciar por um conflito de dados. "
                        "Consulte a viagem novamente."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            self.get_serializer(trip).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
    )
    def finish(self, request, pk=None):
        trip = self.get_object()

        serializer = TripFinishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            trip = finish_trip(
                trip_id=trip.pk,
                actor_id=request.user.pk,
                end_km=serializer.validated_data["end_km"],
                photo=serializer.validated_data["end_odometer_photo"],
            )
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "Não foi possível finalizar por um conflito de dados. "
                        "Consulte a viagem novamente."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            self.get_serializer(trip).data,
            status=status.HTTP_200_OK,
        )