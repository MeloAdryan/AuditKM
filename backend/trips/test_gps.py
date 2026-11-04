from datetime import timedelta
from uuid import uuid4

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from vehicles.models import Vehicle
from .models import Trip, TripLocation


class TripLocationAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.driver = User.objects.create_user(
            username="motorista_gps",
            role=User.Role.DRIVER,
        )

        cls.other_driver = User.objects.create_user(
            username="outro_motorista_gps",
            role=User.Role.DRIVER,
        )

        cls.manager = User.objects.create_user(
            username="gestor_gps",
            role=User.Role.MANAGER,
        )

        cls.administrator = User.objects.create_user(
            username="administrador_gps",
            role=User.Role.ADMIN,
        )

        cls.vehicle = Vehicle.objects.create(
            plate="GPS1A23",
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
        self.url = reverse(
            "trip-locations",
            args=[self.trip.pk],
        )

        self.client.force_authenticate(user=self.driver)

        self.payload = {
            "point_id": str(uuid4()),
            "latitude": "-23.5505200",
            "longitude": "-46.6333080",
            "accuracy_m": "5.00",
            "recorded_at": (
                timezone.now() - timedelta(minutes=5)
            ).isoformat(),
        }

    def send(self, **changes):
        return self.client.post(
            self.url,
            {**self.payload, **changes},
            format="json",
        )

    def complete_trip(self):
        self.trip.status = Trip.Status.COMPLETED
        self.trip.end_km = 15020
        self.trip.end_odometer_photo = "tests/fim.jpg"
        self.trip.ended_at = timezone.now() - timedelta(minutes=1)
        self.trip.save()

    def test_assigned_driver_can_send_point(self):
        response = self.send()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(TripLocation.objects.count(), 1)
        self.assertEqual(response.data["trip"], self.trip.pk)

    def test_anonymous_user_cannot_read_or_send(self):
        self.client.force_authenticate(user=None)

        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.assertEqual(self.send().status_code, 401)

    def test_points_are_ordered_by_capture_time(self):
        later_response = self.send()

        earlier_response = self.send(
            point_id=str(uuid4()),
            recorded_at=(
                timezone.now() - timedelta(minutes=6)
            ).isoformat(),
        )

        self.assertEqual(later_response.status_code, 201)
        self.assertEqual(earlier_response.status_code, 201)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            [point["id"] for point in response.data["results"]],
            [
                earlier_response.data["id"],
                later_response.data["id"],
            ],
        )

    def test_other_driver_cannot_access_trip_points(self):
        self.client.force_authenticate(user=self.other_driver)

        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.send().status_code, 404)

    def test_manager_and_administrator_can_read(self):
        self.assertEqual(self.send().status_code, 201)

        for user in [self.manager, self.administrator]:
            with self.subTest(role=user.role):
                self.client.force_authenticate(user=user)

                response = self.client.get(self.url)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["count"], 1)

    def test_manager_and_administrator_cannot_send(self):
        for user in [self.manager, self.administrator]:
            with self.subTest(role=user.role):
                self.client.force_authenticate(user=user)

                self.assertEqual(self.send().status_code, 403)

        self.assertEqual(TripLocation.objects.count(), 0)

    def test_invalid_coordinates_and_accuracy_are_rejected(self):
        for field, value in [
            ("latitude", "91"),
            ("longitude", "181"),
            ("accuracy_m", "-1"),
        ]:
            with self.subTest(field=field):
                response = self.send(**{field: value})

                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)

        self.assertEqual(TripLocation.objects.count(), 0)

    def test_invalid_capture_times_are_rejected(self):
        invalid_times = [
            self.trip.started_at - timedelta(seconds=1),
            timezone.now() + timedelta(minutes=2),
        ]

        for captured_at in invalid_times:
            with self.subTest(recorded_at=captured_at):
                response = self.send(
                    recorded_at=captured_at.isoformat()
                )

                self.assertEqual(response.status_code, 400)
                self.assertIn("recorded_at", response.data)

    def test_identical_retry_does_not_duplicate_point(self):
        first = self.send()
        second = self.send()

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["id"], second.data["id"])
        self.assertEqual(TripLocation.objects.count(), 1)

    def test_same_identifier_cannot_replace_point_data(self):
        self.assertEqual(self.send().status_code, 201)

        response = self.send(latitude="-23.5605200")

        self.assertEqual(response.status_code, 400)
        self.assertIn("point_id", response.data)
        self.assertEqual(TripLocation.objects.count(), 1)

    def test_completed_trip_accepts_point_captured_before_finish(self):
        self.complete_trip()

        response = self.send()

        self.assertEqual(response.status_code, 201)

    def test_point_captured_after_finish_is_rejected(self):
        self.complete_trip()

        response = self.send(
            recorded_at=(
                self.trip.ended_at + timedelta(seconds=1)
            ).isoformat()
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("recorded_at", response.data)

    def test_planned_trip_cannot_receive_points(self):
        self.trip.status = Trip.Status.PLANNED
        self.trip.save()

        response = self.send()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(TripLocation.objects.count(), 0)