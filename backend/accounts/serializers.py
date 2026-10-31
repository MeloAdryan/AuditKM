from rest_framework import serializers
from .models import User

class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email", "role", "is_staff", "is_superuser")
        read_only_fields = fields
