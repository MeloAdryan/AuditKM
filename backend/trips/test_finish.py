from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.test import APITestCase

from accounts.models import User
from vehicles.models import Vehicle
from .models import Trip


class TripFinishAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.driver = User.objects.create_user(
            username="motorista_finalizacao",
            role=User.Role.DRIVER,
        )

        cls.other_driver = User.objects.create_user(
            username="outro_motorista_finalizacao",
            role=User.Role.DRIVER,
        )

        cls.administrator = User.objects.create_user(
            username="admin_finalizacao",
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
        self.media_root = Path(directory.name)
        self.addCleanup(directory.cleanup)

        settings_override = override_settings(
            MEDIA_ROOT=directory.name
        )

        settings_override.enable()
        self.addCleanup(settings_override.disable)

        self.client.force_authenticate(user=self.driver)

        response = self.client.post(
            reverse("trip-start", args=[self.trip.pk]),
            {
                "start_km": 15000,
                "start_odometer_photo": self.make_photo(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)

        self.trip.refresh_from_db()

        self.url = reverse("trip-finish", args=[self.trip.pk])

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

    def finish(self, end_km=15020, url=None):
        return self.client.post(
            url or self.url,
            {
                "end_km": end_km,
                "end_odometer_photo": self.make_photo(),
            },
            format="multipart",
        )

    def test_assigned_driver_can_finish(self):
        original_start_photo = self.trip.start_odometer_photo.name

        response = self.finish()

        self.assertEqual(response.status_code, 200)

        self.trip.refresh_from_db()
        self.vehicle.refresh_from_db()

        self.assertEqual(self.trip.status, Trip.Status.COMPLETED)
        self.assertEqual(self.trip.end_km, 15020)
        self.assertEqual(self.trip.traveled_km, 20)
        self.assertIsNotNone(self.trip.ended_at)
        self.assertEqual(self.vehicle.current_km, 15020)

        self.assertEqual(
            self.trip.start_odometer_photo.name,
            original_start_photo,
        )

        self.assertTrue(
            self.trip.end_odometer_photo.storage.exists(
                self.trip.end_odometer_photo.name
            )
        )

    def test_final_photo_is_required(self):
        response = self.client.post(
            self.url,
            {"end_km": 15020},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("end_odometer_photo", response.data)

        self.trip.refresh_from_db()

        self.assertEqual(self.trip.status, Trip.Status.IN_PROGRESS)

    def test_final_odometer_is_required(self):
        response = self.client.post(
            self.url,
            {"end_odometer_photo": self.make_photo()},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("end_km", response.data)

    def test_final_odometer_cannot_be_below_start(self):
        response = self.finish(end_km=14999)

        self.assertEqual(response.status_code, 400)
        self.assertIn("end_km", response.data)

        self.trip.refresh_from_db()
        self.vehicle.refresh_from_db()

        self.assertEqual(self.trip.status, Trip.Status.IN_PROGRESS)
        self.assertEqual(self.vehicle.current_km, 15000)

    def test_planned_trip_cannot_be_finished(self):
        planned_trip = Trip.objects.create(
            driver=self.driver,
            vehicle=self.vehicle,
            origin="Empresa A",
            destination="Fazenda B",
        )

        response = self.finish(
            url=reverse("trip-finish", args=[planned_trip.pk])
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.data)

    def test_trip_cannot_be_finished_twice(self):
        self.assertEqual(self.finish().status_code, 200)

        self.trip.refresh_from_db()

        original_ended_at = self.trip.ended_at
        original_photo = self.trip.end_odometer_photo.name

        self.assertEqual(
            self.finish(end_km=15030).status_code,
            400,
        )

        self.trip.refresh_from_db()
        self.vehicle.refresh_from_db()

        self.assertEqual(self.trip.ended_at, original_ended_at)
        self.assertEqual(self.trip.end_km, 15020)
        self.assertEqual(self.vehicle.current_km, 15020)

        self.assertEqual(
            self.trip.end_odometer_photo.name,
            original_photo,
        )

    def test_other_driver_cannot_finish(self):
        self.client.force_authenticate(user=self.other_driver)

        self.assertEqual(self.finish().status_code, 404)

    def test_administrator_cannot_finish(self):
        self.client.force_authenticate(user=self.administrator)

        self.assertEqual(self.finish().status_code, 403)

    def test_vehicle_odometer_cannot_regress(self):
        self.vehicle.current_km = 15050
        self.vehicle.save()

        response = self.finish(end_km=15030)

        self.assertEqual(response.status_code, 400)
        self.assertIn("end_km", response.data)

        self.vehicle.refresh_from_db()

        self.assertEqual(self.vehicle.current_km, 15050)

    def test_failure_updating_vehicle_rolls_back_finish(self):
        with patch(
            "vehicles.models.Vehicle.save",
            side_effect=RuntimeError("Falha simulada"),
        ):
            with self.assertRaises(RuntimeError):
                self.finish()

        self.trip.refresh_from_db()
        self.vehicle.refresh_from_db()

        self.assertEqual(self.trip.status, Trip.Status.IN_PROGRESS)
        self.assertIsNone(self.trip.end_km)
        self.assertIsNone(self.trip.ended_at)
        self.assertFalse(self.trip.end_odometer_photo)
        self.assertEqual(self.vehicle.current_km, 15000)

        saved_files = [
            path
            for path in self.media_root.rglob("*")
            if path.is_file()
        ]

        self.assertEqual(len(saved_files), 1)