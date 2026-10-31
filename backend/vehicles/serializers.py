from django.utils import timezone
from rest_framework import serializers

from .models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle

        fields = [
            "id",
            "plate",
            "brand",
            "model",
            "year",
            "color",
            "current_km",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_year(self, value):
        if value > timezone.localdate().year + 1:
            raise serializers.ValidationError(
                "O ano não pode ser superior ao próximo ano."
            )

        return value

    def validate_current_km(self, value):
        if self.instance is not None:
            if value != self.instance.current_km:
                raise serializers.ValidationError(
                    "A quilometragem não pode ser alterada pela edição cadastral."
                )

        return value