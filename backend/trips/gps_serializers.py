from rest_framework import serializers

from .models import TripLocation



class TripLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripLocation
        
        fields = [
            "id",
            "trip",
            "point_id",
            "latitude",
            "longitude",
            "accuracy_m",
            "recorded_at",
            "received_at",
            
        ]
        
        read_only_fields = [
            "id",
            "trip",
            "received_at",
        ]

        validators = []

    def validate(self, attrs):
        allowed_fields = {
            "point_id",
            "latitude",
            "longitude",
            "accuracy_m",
            "recorded_at",
        }

        unexpected_fields = set(self.initial_data) - allowed_fields

        if unexpected_fields:
            raise serializers.ValidationError(
                {
                    field: "Este campo não pode ser enviado no ponto GPS."
                    for field in sorted(unexpected_fields)
                }
            )

        return attrs