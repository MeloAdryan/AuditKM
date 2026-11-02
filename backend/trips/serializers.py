from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


from accounts.models import User
from vehicles.models import Vehicle
from .models import Trip



class TripSerializer(serializers.ModelSerializer):
    driver = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(
            role=User.Role.DRIVER,
            is_active=True,
        )
    )

    vehicle = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.filter(
            status=Vehicle.Status.ACTIVE,
        )
    )

    driver_username = serializers.CharField(
        source="driver.username",
        read_only=True,
    )

    vehicle_plate = serializers.CharField(
        source="vehicle.plate",
        read_only=True,
    )

    traveled_km = serializers.IntegerField(read_only=True)

    class Meta:
        model = Trip
        fields = [ 
            "id",
            "driver",
            "driver_username",
            "vehicle",
            "vehicle_plate",
            "origin",
            "destination",
            "notes",
            "status",
            "start_km",
            "end_km",
            "started_at",
            "traveled_km",
            "created_at",
            "updated_at",
        ]
        
        read_only_fields = [
                      "id",
                      "status",
                      "start_km",
                      "end_km",
                      "started_at",
                      "ended_at",
                      "created_at",
                      "updated_at",
    ]
        
    def validate(self, attrs):
        allowed_fields = {
            "driver",
            "vehicle",
            "origin",
            "destination",
            "notes",
        }

        unexpected_fields = set(self.initial_data) - allowed_fields

        if unexpected_fields:
            raise serializers.ValidationError(
                {
                    field: "Este campo não pode ser enviado no planejamento."
                    for field in sorted(unexpected_fields)
                }
            )

        return attrs

    def create(self, validated_data):
        trip = Trip(
            **validated_data,
            status=Trip.Status.PLANNED,
        )

        try:
            trip.full_clean()
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise serializers.ValidationError(
                    exc.message_dict
                ) from exc

            raise serializers.ValidationError(
                {"detail": exc.messages}
            ) from exc

        trip.save()

        return trip