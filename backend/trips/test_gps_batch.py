from datetime import timedelta
from uuid import uuid4

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User 
from vehicles.models import Vehicle 
from .models import Trip, TripLocation

class TripLocationBatcheAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.driver = User.objects.create_user(
            username="motorista_lote",
            role=User.Role.DRIVER,
        )
        cls.other_driver = User.objects.create_user(
            username="outro_motorista_lote",
            role=User.Role.DRIVER,
        )
        cls.administrator = User.objects.create_user(
            username="administrador_lote",
            role=User.Role.ADMIN,
        )

        cls.vehicle = Vehicle.objects.create(
            plate="LOT1A23",
            brand="Fiat",
            model="Strada",
            year=2024,
            current_km=15000,
        )

        cls.started_at = timezone.now() - timedelta(minutes=10)

        cls.trip = Trip.objects.create(
            driver=cls.driver,
            vehicle=cls.vehicle,
            origin="Empresa A",
            destination="Fazenda A",
            status=Trip.Status.IN_PROGRESS,
            start_km=15000,
            start_odometer_photo="tests/inicio.jpg",
            started_at=cls.started_at,
        )

    def setUp(self):
        self.client.force_authenticate(user=self.driver)

        self.url = reverse(
            "trip-locations-batch",
            kwargs={"trip_id": self.trip.pk},
        )

    def make_point(self, seconds=60):
        return {
            "point_id": str(uuid4()),
            "latitude": "-9.9740000",
            "longitude": "-67.8100000",
            "accuracy_m": "12.00",
            "recorded_at": (
                self.started_at + timedelta(seconds=seconds)
            ).isoformat(),
        }

    def send_points(self, points):
        return self.client.post(
            self.url,
            {"points": points},
            format="json",
        )

    def test_assigned_driver_can_send_batch(self):
        response = self.send_points(
            [self.make_point(60), self.make_point(120)]
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["received"], 2)
        self.assertEqual(response.data["created"], 2)
        self.assertEqual(response.data["existing"], 0)
        self.assertEqual(
            TripLocation.objects.filter(trip=self.trip).count(),
            2,
        )

    def test_identical_retry_does_not_duplicate_points(self):
        points = [self.make_point(60), self.make_point(120)]

        first = self.send_points(points)
        second = self.send_points(points)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["created"], 0)
        self.assertEqual(second.data["existing"], 2)
        self.assertEqual(TripLocation.objects.count(), 2)

    def test_batch_can_mix_existing_and_new_points(self):
        existing = self.make_point(60)
        self.assertEqual(
            self.send_points([existing]).status_code,
            201,
        )

        response = self.send_points(
            [existing, self.make_point(120)]
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["created"], 1)
        self.assertEqual(response.data["existing"], 1)
        self.assertEqual(TripLocation.objects.count(), 2)

    def test_conflicting_identifier_rolls_back_new_points(self):
        existing = self.make_point(60)
        self.assertEqual(
            self.send_points([existing]).status_code,
            201,
        )

        changed = {
            **existing,
            "latitude": "-9.9750000",
        }

        response = self.send_points(
            [self.make_point(120), changed]
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            int(response.data["point_index"]),
            1,
        )
        self.assertEqual(TripLocation.objects.count(), 1)

        location = TripLocation.objects.get(
            point_id=existing["point_id"],
        )
        self.assertEqual(
            str(location.latitude),
            "-9.9740000",
        )

    def test_point_before_start_rolls_back_entire_batch(self):
        response = self.send_points(
            [self.make_point(60), self.make_point(-60)]
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            int(response.data["point_index"]),
            1,
        )
        self.assertEqual(TripLocation.objects.count(), 0)

    def test_invalid_coordinate_rejects_entire_batch(self):
        invalid = {
            **self.make_point(120),
            "latitude": "91.0000000",
        }

        response = self.send_points(
            [self.make_point(60), invalid]
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(TripLocation.objects.count(), 0)

    def test_duplicate_identifier_inside_batch_is_rejected(self):
        point = self.make_point()

        response = self.send_points([point, point])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(TripLocation.objects.count(), 0)

    def test_empty_batch_is_rejected(self):
        response = self.send_points([])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(TripLocation.objects.count(), 0)

    def test_batch_above_limit_is_rejected(self):
        response = self.send_points(
            [self.make_point() for _ in range(101)]
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(TripLocation.objects.count(), 0)

    def test_batch_at_limit_is_accepted(self):
        response = self.send_points(
            [self.make_point() for _ in range(100)]
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["created"], 100)
        self.assertEqual(TripLocation.objects.count(), 100)

    def test_anonymous_user_cannot_send_batch(self):
        self.client.force_authenticate(user=None)

        response = self.send_points([self.make_point()])

        self.assertEqual(response.status_code, 401)
        self.assertEqual(TripLocation.objects.count(), 0)

    def test_other_driver_cannot_send_batch(self):
        self.client.force_authenticate(user=self.other_driver)

        response = self.send_points([self.make_point()])

        self.assertEqual(response.status_code, 404)
        self.assertEqual(TripLocation.objects.count(), 0)

    def test_administrator_cannot_send_batch(self):
        self.client.force_authenticate(
            user=self.administrator,
        )

        response = self.send_points([self.make_point()])

        self.assertEqual(response.status_code, 403)
        self.assertEqual(TripLocation.objects.count(), 0)

    def test_planned_trip_cannot_receive_batch(self):
        self.trip.status = Trip.Status.PLANNED
        self.trip.save(update_fields=["status"])

        response = self.send_points([self.make_point()])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(TripLocation.objects.count(), 0)

    def test_unexpected_batch_field_is_rejected(self):
        response = self.client.post(
            self.url,
            {
                "points": [self.make_point()],
                "driver": self.other_driver.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(TripLocation.objects.count(), 0)

    def test_completed_trip_accepts_point_captured_before_end(self):
        self.trip.status = Trip.Status.COMPLETED
        self.trip.ended_at = (
            self.started_at + timedelta(minutes=5)
        )
        self.trip.save(
            update_fields=["status", "ended_at"],
        )

        response = self.send_points([self.make_point(120)])

        self.assertEqual(response.status_code, 201)
        self.assertEqual(TripLocation.objects.count(), 1)

    def test_point_after_end_rolls_back_entire_batch(self):
        self.trip.status = Trip.Status.COMPLETED
        self.trip.ended_at = (
            self.started_at + timedelta(minutes=5)
        )
        self.trip.save(
            update_fields=["status", "ended_at"],
        )

        response = self.send_points(
            [self.make_point(120), self.make_point(360)]
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(TripLocation.objects.count(), 0)
        
    def test_unexpected_point_field_rejects_entire_batch(self):
        invalid = {
            **self.make_point(120),
            "trip": self.trip.pk,
        }

        response = self.send_points(
            [self.make_point(60), invalid]
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(TripLocation.objects.count(), 0)
        self.assertIn("trip", response.data["points"][1])