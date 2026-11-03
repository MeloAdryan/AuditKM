from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from django.urls import reverse
from PIL import Image
from rest_framework.test import APITestCase

from accounts.models import User
from vehicles.models import Vehicle
from .models import Trip
from .serializers import TripStartSerializer


class TripAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user(
            username="gestor_viagens",
            role=User.Role.MANAGER,
        )

        cls.administrator = User.objects.create_user(
            username="admin_viagens",
            role=User.Role.ADMIN,
        )

        cls.driver = User.objects.create_user(
            username="motorista_um",
            role=User.Role.DRIVER,
        )

        cls.other_driver = User.objects.create_user(
            username="motorista_dois",
            role=User.Role.DRIVER,
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

        cls.other_trip = Trip.objects.create(
            driver=cls.other_driver,
            vehicle=cls.vehicle,
            origin="Empresa A",
            destination="Fazenda B",
        )

    def setUp(self):
        self.list_url = reverse("trip-list")

        self.payload = {
            "driver": self.driver.pk,
            "vehicle": self.vehicle.pk,
            "origin": "Empresa A",
            "destination": "Fazenda C",
            "notes": "Planejamento de teste",
        }

    def test_anonymous_user_cannot_list(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 401)

    def test_manager_and_administrator_can_plan(self):
        for user in [self.manager, self.administrator]:
            with self.subTest(role=user.role):
                self.client.force_authenticate(user=user)

                response = self.client.post(
                    self.list_url,
                    self.payload,
                    format="json",
                )

                self.assertEqual(response.status_code, 201)

                trip = Trip.objects.get(pk=response.data["id"])

                self.assertEqual(trip.status, Trip.Status.PLANNED)
                self.assertEqual(trip.driver_id, self.driver.pk)
                self.assertIsNone(trip.started_at)

    def test_driver_cannot_plan(self):
        self.client.force_authenticate(user=self.driver)

        response = self.client.post(
            self.list_url,
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Trip.objects.count(), 2)

    def test_driver_sees_only_own_trips(self):
        self.client.force_authenticate(user=self.driver)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["id"],
            self.trip.pk,
        )

    def test_driver_cannot_retrieve_another_drivers_trip(self):
        self.client.force_authenticate(user=self.driver)

        response = self.client.get(
            reverse("trip-detail", args=[self.other_trip.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_operational_fields_are_rejected(self):
        self.client.force_authenticate(user=self.manager)

        for field, value in [
            ("status", "COMPLETED"),
            ("start_km", 15000),
            ("started_at", "2026-11-02T10:00:00Z"),
            ("start_odometer_photo", "foto.jpg"),
        ]:
            with self.subTest(field=field):
                response = self.client.post(
                    self.list_url,
                    {**self.payload, field: value},
                    format="json",
                )

                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)

        self.assertEqual(Trip.objects.count(), 2)

    def test_inactive_vehicle_cannot_be_selected(self):
        self.vehicle.status = Vehicle.Status.INACTIVE
        self.vehicle.save()

        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            self.list_url,
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("vehicle", response.data)

    def test_manager_cannot_be_assigned_as_driver(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            self.list_url,
            {**self.payload, "driver": self.manager.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("driver", response.data)
        
class TripStartSerializerTests(SimpleTestCase):
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

    def test_valid_start_data_is_accepted(self):
        serializer = TripStartSerializer(
            data={
                "start_km": 15000,
                "start_odometer_photo": self.make_photo(),
            }
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            serializer.validated_data["start_km"],
            15000,
        )

    def test_photo_is_required(self):
        serializer = TripStartSerializer(
            data={"start_km": 15000}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "start_odometer_photo",
            serializer.errors,
        )

    def test_odometer_is_required(self):
        serializer = TripStartSerializer(
            data={
                "start_odometer_photo": self.make_photo(),
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("start_km", serializer.errors)

    def test_negative_odometer_is_rejected(self):
        serializer = TripStartSerializer(
            data={
                "start_km": -1,
                "start_odometer_photo": self.make_photo(),
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("start_km", serializer.errors)

    def test_invalid_image_is_rejected(self):
        fake_photo = SimpleUploadedFile(
            "hodometro.jpg",
            b"arquivo que nao e uma imagem",
            content_type="image/jpeg",
        )

        serializer = TripStartSerializer(
            data={
                "start_km": 15000,
                "start_odometer_photo": fake_photo,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "start_odometer_photo",
            serializer.errors,
        )

    def test_client_cannot_choose_start_time(self):
        serializer = TripStartSerializer(
            data={
                "start_km": 15000,
                "start_odometer_photo": self.make_photo(),
                "started_at": "2026-11-02T10:00:00Z",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("started_at", serializer.errors)