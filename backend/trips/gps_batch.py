from django.db import transaction
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from accounts.models import User
from .gps_serializers import TripLocationSerializer
from .gps_services import register_trip_location
from .gps_views import TripLocationView


class TripLocationBatchSerializer(serializers.Serializer):
    points = TripLocationSerializer(
        many=True,
        allow_empty=False,
        max_length=100,
    )

    def validate(self, attrs):
        unexpected_fields = set(self.initial_data) - {"points"}

        if unexpected_fields:
            raise serializers.ValidationError(
                {
                    field: "Este campo não pode ser enviado no lote."
                    for field in sorted(unexpected_fields)
                }
            )

        point_ids = [
            point["point_id"]
            for point in attrs["points"]
        ]

        if len(point_ids) != len(set(point_ids)):
            raise serializers.ValidationError(
                {
                    "points": (
                        "O mesmo point_id não pode aparecer "
                        "mais de uma vez dentro do lote."
                    )
                }
            )

        return attrs


@transaction.atomic
def register_trip_location_batch(*, trip_id, actor_id, points):
    locations = []
    created_count = 0

    for index, point in enumerate(points):
        try:
            location, created = register_trip_location(
                trip_id=trip_id,
                actor_id=actor_id,
                data=point,
            )
        except serializers.ValidationError as error:
            raise serializers.ValidationError(
                {
                    "point_index": index,
                    "errors": error.detail,
                }
            ) from error

        locations.append(location)
        created_count += int(created)

    return locations, created_count


class TripLocationBatchView(TripLocationView):
    http_method_names = ["post", "options"]

    def post(self, request, trip_id):
        if (
            not request.user.is_active
            or request.user.role != User.Role.DRIVER
        ):
            raise PermissionDenied(
                "Somente motoristas ativos podem enviar pontos GPS."
            )

        trip = self.get_trip(request, trip_id)

        serializer = TripLocationBatchSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        locations, created_count = register_trip_location_batch(
            trip_id=trip.pk,
            actor_id=request.user.pk,
            points=serializer.validated_data["points"],
        )

        return Response(
            {
                "received": len(locations),
                "created": created_count,
                "existing": len(locations) - created_count,
                "results": TripLocationSerializer(
                    locations,
                    many=True,
                ).data,
            },
            status=(
                status.HTTP_201_CREATED
                if created_count
                else status.HTTP_200_OK
            ),
        )