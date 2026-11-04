from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


from accounts.models import User
from .gps_serializers import TripLocationSerializer
from .gps_services import register_trip_location
from .models import Trip


class TripLocationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_trip(self, request, trip_id):
        user = request.user
        queryset = Trip.objects.all()
        
        if user. is_superuser or user.role in {
            User.Role.ADMIN,
            User.Role.MANAGER,
        }:
            return get_object_or_404(queryset, pk=trip_id)

        if user.role == User.Role.DRIVER:
            return get_object_or_404(
                queryset.filter(driver=user),
                pk=trip_id,
            )

        raise PermissionDenied(
            "Seu perfil não permite consultar este percurso."
        )

    def get(self, request, trip_id):
        trip = self.get_trip(request, trip_id)

        locations = trip.locations.order_by(
            "recorded_at",
            "id",
        )

        paginator = PageNumberPagination()

        page = paginator.paginate_queryset(
            locations,
            request,
            view=self,
        )

        serializer = TripLocationSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(serializer.data)

    def post(self, request, trip_id):
        if request.user.role != User.Role.DRIVER:
            raise PermissionDenied(
                "Somente motoristas podem enviar pontos GPS."
            )

        trip = self.get_trip(request, trip_id)

        serializer = TripLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        location, created = register_trip_location(
            trip_id=trip.pk,
            actor_id=request.user.pk,
            data=serializer.validated_data,
        )

        response_status = (
            status.HTTP_201_CREATED
            if created
            else status.HTTP_200_OK
        )

        return Response(
            TripLocationSerializer(location).data,
            status=response_status,
        )