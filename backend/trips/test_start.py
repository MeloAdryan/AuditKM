from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.test import APITestCase

from accounts.models import User
from vehicles.models import Vehicle
from .models import Trip


class TripStartAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.driver = User.objects.create_user(
            username="motorista_inicio",
            role=User.Role.DRIVER,
        )

        cls.other_driver = User.objects.create_user(
            username="outro_motorista_inicio",
            role=User.Role.DRIVER,
        )

        cls.administrator = User.objects.create_user(
            username="administrador_inicio",
            role=User.Role.ADMIN,
        )

        cls.vehicle = Vehicle.objects.create(
            plate="ABC1D23",
            brand="Fiat",
            model="Strada",
            year=2024,
            current_km=15000,
        )

        cls.trip = Trip.objects.create(
            driver=cls.driver,
            vehicle=cls.vehicle,
            origin="Empresa A",
            destination="Fazenda A",
        )

    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)

        settings_override = override_settings(
            MEDIA_ROOT=directory.name
        )

        settings_override.enable()
        self.addCleanup(settings_override.disable)

        self.url = reverse("trip-start", args=[self.trip.pk])
        self.client.force_authenticate(user=self.driver)

    def make_photo(self):
        buffer = BytesIO()

        Image.new(
            "RGB",
            (32, 32),
            color="white",
        ).save(buffer, format="JPEG")

        return SimpleUploadedFile(
            "hodometro.jpg",
            buffer.getvalue(),
            content_type="image/jpeg",
        )

    def start(self, url=None, start_km=15000):
        return self.client.post(
            url or self.url,
            {
                "start_km": start_km,
                "start_odometer_photo": self.make_photo(),
            },
            format="multipart",
        )

    def test_assigned_driver_can_start(self):
        response = self.start()

        self.assertEqual(response.status_code, 200)

        self.trip.refresh_from_db()

        self.assertEqual(
            self.trip.status,
            Trip.Status.IN_PROGRESS,
        )

        self.assertEqual(self.trip.start_km, 15000)
        self.assertIsNotNone(self.trip.started_at)

        self.assertTrue(
            self.trip.start_odometer_photo.storage.exists(
                self.trip.start_odometer_photo.name
            )
        )

    def test_photo_is_required(self):
        response = self.client.post(
            self.url,
            {"start_km": 15000},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)

        self.trip.refresh_from_db()

        self.assertEqual(self.trip.status, Trip.Status.PLANNED)

    def test_anonymous_user_cannot_start(self):
        self.client.force_authenticate(user=None)

        self.assertEqual(self.start().status_code, 401)

    def test_other_driver_cannot_start(self):
        self.client.force_authenticate(user=self.other_driver)

        self.assertEqual(self.start().status_code, 404)

    def test_administrator_cannot_start(self):
        self.client.force_authenticate(user=self.administrator)

        self.assertEqual(self.start().status_code, 403)

    def test_odometer_below_vehicle_value_is_rejected(self):
        response = self.start(start_km=14999)

        self.assertEqual(response.status_code, 400)
        self.assertIn("start_km", response.data)

        self.trip.refresh_from_db()

        self.assertEqual(self.trip.status, Trip.Status.PLANNED)

    def test_inactive_vehicle_cannot_start(self):
        self.vehicle.status = Vehicle.Status.INACTIVE
        self.vehicle.save()

        response = self.start()

        self.assertEqual(response.status_code, 400)
        self.assertIn("vehicle", response.data)

    def test_trip_cannot_start_twice(self):
        self.assertEqual(self.start().status_code, 200)

        self.trip.refresh_from_db()
        original_started_at = self.trip.started_at
        original_photo = self.trip.start_odometer_photo.name

        self.assertEqual(self.start().status_code, 400)

        self.trip.refresh_from_db()

        self.assertEqual(self.trip.started_at, original_started_at)
        self.assertEqual(
            self.trip.start_odometer_photo.name,
            original_photo,
        )

    def test_vehicle_cannot_have_two_active_trips(self):
        self.assertEqual(self.start().status_code, 200)

        other_trip = Trip.objects.create(
            driver=self.other_driver,
            vehicle=self.vehicle,
            origin="Empresa A",
            destination="Fazenda B",
        )

        self.client.force_authenticate(user=self.other_driver)

        response = self.start(
            url=reverse("trip-start", args=[other_trip.pk])
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("vehicle", response.data)

    def test_driver_cannot_have_two_active_trips(self):
        self.assertEqual(self.start().status_code, 200)

        other_vehicle = Vehicle.objects.create(
            plate="DEF4G56",
            brand="Toyota",
            model="Hilux",
            year=2024,
            current_km=10000,
        )

        other_trip = Trip.objects.create(
            driver=self.driver,
            vehicle=other_vehicle,
            origin="Empresa A",
            destination="Fazenda B",
        )

        response = self.start(
            url=reverse("trip-start", args=[other_trip.pk])
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("driver", response.data)