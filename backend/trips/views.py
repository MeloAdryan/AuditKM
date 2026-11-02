from rest_framework import mixins, viewsets

from accounts.models import User
from .models import Trip
from .permissions import TripPermission
from .serializers import TripSerializer


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