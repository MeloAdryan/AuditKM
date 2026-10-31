from rest_framework import mixins, viewsets

from .models import Vehicle
from .permissions import VehiclePermission
from .serializers import VehicleSerializer


class VehicleViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Vehicle.objects.all().order_by("plate")
    serializer_class = VehicleSerializer
    permission_classes = [VehiclePermission]