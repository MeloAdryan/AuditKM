from django.urls import path
from rest_framework.routers import SimpleRouter

from .gps_batch import TripLocationBatchView
from .gps_views import TripLocationView
from .views import TripViewSet


router = SimpleRouter()
router.register("trips", TripViewSet, basename="trip")

urlpatterns = [
    path(
        "trips/<int:trip_id>/locations/",
        TripLocationView.as_view(),
        name="trip-locations",
    ),
    path(
        "trips/<int:trip_id>/locations/batch/",
        TripLocationBatchView.as_view(),
        name="trip-locations-batch",
    ),
]

urlpatterns += router.urls