from rest_framework.pagination import CursorPagination


from .gps_serializers import TripLocationSerializer
from .gps_views import TripLocationView


class TripTrackPagination(CursorPagination):
    page_size = 500
    ordering = ("recorded_at", "id")
    cursor_query_param = "cursor"


class TripTrackView(TripLocationView):
    http_method_names = ["get", "head", "options"]

    def get(self, request, trip_id):
        trip = self.get_trip(request, trip_id)

        locations = trip.locations.all()

        paginator = TripTrackPagination()

        page = paginator.paginate_queryset(
            locations,
            request,
            view=self,
        )

        serializer = TripLocationSerializer(
            page,
            many=True,
        )

        response = paginator.get_paginated_response(
            serializer.data
        )

        response["Cache-Control"] = "private, no-store"

        return response