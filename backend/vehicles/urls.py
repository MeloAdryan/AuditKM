from rest_framework.routers import SimpleRouter

from .views import VehicleViewSet


router = SimpleRouter()
router.register("vehicles", VehicleViewSet, basename="vehicle")

urlpatterns = router.urls