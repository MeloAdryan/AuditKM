from datetime import timedelta
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from accounts.models import User
from vehicles.models import Vehicle
from .models import Trip
from .serializers import TripFinishSerializer


def make_photo(image_format="JPEG"):
    buffer = BytesIO()

    Image.new(
        "RGB",
        (32, 32),
        color="white",
    ).save(buffer, format=image_format)

    extensions = {
        "JPEG": "jpg",
        "PNG": "png",
        "GIF": "gif",
    }

    content_types = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "GIF": "image/gif",
    }

    return SimpleUploadedFile(
        f"hodometro.{extensions[image_format]}",
        buffer.getvalue(),
        content_type=content_types[image_format],
    )


class TripFinishSerializerValidationTests(SimpleTestCase):
    def test_jpeg_and_png_are_accepted(self):
        for image_format in ["JPEG", "PNG"]:
            with self.subTest(image_format=image_format):
                serializer = TripFinishSerializer(
                    data={
                        "end_km": 15020,
                        "end_odometer_photo": make_photo(image_format),
                    }
                )

                self.assertTrue(
                    serializer.is_valid(),
                    serializer.errors,
                )

    def test_gif_is_rejected(self):
        serializer = TripFinishSerializer(
            data={
                "end_km": 15020,
                "end_odometer_photo": make_photo("GIF"),
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "end_odometer_photo",
            serializer.errors,
        )

    def test_photo_above_size_limit_is_rejected(self):
        photo = make_photo()
        photo.size = 10 * 1024 * 1024 + 1

        serializer = TripFinishSerializer(
            data={
                "end_km": 15020,
                "end_odometer_photo": photo,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "end_odometer_photo",
            serializer.errors,
        )

    def test_photo_at_size_limit_is_accepted(self):
        photo = make_photo()
        photo.size = 10 * 1024 * 1024

        serializer = TripFinishSerializer(
            data={
                "end_km": 15020,
                "end_odometer_photo": photo,
            }
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_unexpected_fields_are_rejected(self):
        for field, value in [
            ("status", "COMPLETED"),
            ("ended_at", "2026-11-05T12:00:00Z"),
            ("driver", 999),
            ("start_km", 1),
        ]:
            with self.subTest(field=field):
                serializer = TripFinishSerializer(
                    data={
                        "end_km": 15020,
                        "end_odometer_photo": make_photo(),
                        field: value,
                    }
                )

                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)


class TripFinishPhotoAPIValidationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.driver = User.objects.create_user(
            username="motorista_validacao_foto",
            role=User.Role.DRIVER,
        )

        cls.vehicle = Vehicle.objects.create(
            plate="VAL1A23",
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
            status=Trip.Status.IN_PROGRESS,
            start_km=15000,
            start_odometer_photo="tests/inicio.jpg",
            started_at=timezone.now() - timedelta(minutes=10),
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

    def test_gif_returns_400_and_preserves_trip(self):
        response = self.client.post(
            reverse("trip-finish", args=[self.trip.pk]),
            {
                "end_km": 15020,
                "end_odometer_photo": make_photo("GIF"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("end_odometer_photo", response.data)

        self.trip.refresh_from_db()
        self.vehicle.refresh_from_db()

        self.assertEqual(
            self.trip.status,
            Trip.Status.IN_PROGRESS,
        )

        self.assertIsNone(self.trip.end_km)
        self.assertIsNone(self.trip.ended_at)
        self.assertFalse(self.trip.end_odometer_photo)
        self.assertEqual(self.vehicle.current_km, 15000)

        saved_files = [
            path
            for path in self.media_root.rglob("*")
            if path.is_file()
        ]

        self.assertEqual(saved_files, [])