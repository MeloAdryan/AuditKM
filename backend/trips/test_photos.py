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


class TripPhotoAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.driver = User.objects.create_user(
            username="motorista_fotos",
            role=User.Role.DRIVER,
        )
        cls.other_driver = User.objects.create_user(
            username="outro_motorista_fotos",
            role=User.Role.DRIVER,
        )
        cls.manager = User.objects.create_user(
            username="gestor_fotos",
            role=User.Role.MANAGER,
        )
        cls.administrator = User.objects.create_user(
            username="administrador_fotos",
            role=User.Role.ADMIN,
        )
        cls.vehicle = Vehicle.objects.create(
            plate="FOT1A23",
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
            MEDIA_ROOT=directory.name,
        )
        settings_override.enable()
        self.addCleanup(settings_override.disable)

        buffer = BytesIO()
        Image.new("RGB", (32, 32), color="white").save(
            buffer,
            format="JPEG",
        )
        self.photo_bytes = buffer.getvalue()

        self.trip.start_odometer_photo.save(
            "inicio.jpg",
            SimpleUploadedFile(
                "inicio.jpg",
                self.photo_bytes,
                content_type="image/jpeg",
            ),
            save=True,
        )
        self.trip.end_odometer_photo.save(
            "final.jpg",
            SimpleUploadedFile(
                "final.jpg",
                self.photo_bytes,
                content_type="image/jpeg",
            ),
            save=True,
        )

    def photo_url(self, stage="start"):
        return reverse(
            "trip-odometer-photo",
            kwargs={
                "pk": self.trip.pk,
                "stage": stage,
            },
        )

    def assert_photo_available(self, user, stage="start"):
        self.client.force_authenticate(user=user)
        response = self.client.get(self.photo_url(stage))

        try:
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.streaming)
            self.assertEqual(
                response["Content-Type"],
                "image/jpeg",
            )
            self.assertEqual(
                response["Cache-Control"],
                "private, no-store",
            )
            self.assertEqual(
                response["X-Content-Type-Options"],
                "nosniff",
            )
            self.assertEqual(
                b"".join(response.streaming_content),
                self.photo_bytes,
            )
        finally:
            response.close()

    def test_assigned_driver_can_read_start_photo(self):
        self.assert_photo_available(self.driver)

    def test_assigned_driver_can_read_end_photo(self):
        self.assert_photo_available(self.driver, "end")

    def test_manager_can_read_photos(self):
        for stage in ("start", "end"):
            with self.subTest(stage=stage):
                self.assert_photo_available(self.manager, stage)

    def test_administrator_can_read_photos(self):
        for stage in ("start", "end"):
            with self.subTest(stage=stage):
                self.assert_photo_available(
                    self.administrator,
                    stage,
                )

    def test_anonymous_user_cannot_read_photos(self):
        for stage in ("start", "end"):
            with self.subTest(stage=stage):
                response = self.client.get(
                    self.photo_url(stage),
                )
                self.assertEqual(response.status_code, 401)

    def test_other_driver_cannot_read_photos(self):
        self.client.force_authenticate(user=self.other_driver)

        for stage in ("start", "end"):
            with self.subTest(stage=stage):
                response = self.client.get(
                    self.photo_url(stage),
                )
                self.assertEqual(response.status_code, 404)

    def test_inactive_driver_cannot_read_photo(self):
        self.driver.is_active = False
        self.driver.save(update_fields=["is_active"])
        self.client.force_authenticate(user=self.driver)

        response = self.client.get(self.photo_url())

        self.assertEqual(response.status_code, 403)

    def test_missing_photo_field_returns_404(self):
        self.trip.start_odometer_photo = ""
        self.trip.save(update_fields=["start_odometer_photo"])
        self.client.force_authenticate(user=self.driver)

        response = self.client.get(self.photo_url())

        self.assertEqual(response.status_code, 404)

    def test_missing_file_returns_404(self):
        photo = self.trip.start_odometer_photo
        photo.storage.delete(photo.name)
        self.client.force_authenticate(user=self.driver)

        response = self.client.get(self.photo_url())

        self.assertEqual(response.status_code, 404)

    def test_unknown_trip_returns_404(self):
        self.client.force_authenticate(user=self.administrator)

        response = self.client.get(
            reverse(
                "trip-odometer-photo",
                kwargs={
                    "pk": self.trip.pk + 1000,
                    "stage": "start",
                },
            ),
        )

        self.assertEqual(response.status_code, 404)