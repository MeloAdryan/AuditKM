from datetime import timedelta
from urllib.parse import urlsplit
from uuid import uuid4

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from vehicles.models import Vehicle
from .models import Trip, TripLocation


class TripTrackAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.driver = User.objects.create_user(
            username="motorista_percurso",
            role=User.Role.DRIVER,
        )
        cls.other_driver = User.objects.create_user(
            username="outro_motorista_percurso",
            role=User.Role.DRIVER,
        )
        cls.manager = User.objects.create_user(
            username="gestor_percurso",
            role=User.Role.MANAGER,
        )
        cls.administrator = User.objects.create_user(
            username="administrador_percurso",
            role=User.Role.ADMIN,
        )

        cls.vehicle = Vehicle.objects.create(
            plate="CUR1A23",
            brand="Fiat",
            model="Strada",
            year=2024,
            current_km=15000,
        )

        cls.started_at = timezone.now() - timedelta(hours=2)

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
            "trip-track",
            kwargs={"trip_id": self.trip.pk},
        )

    def create_points(self, count, same_time=False):
        points = [
            TripLocation(
                trip=self.trip,
                point_id=uuid4(),
                latitude="-9.9740000",
                longitude="-67.8100000",
                accuracy_m="25.00",
                recorded_at=(
                    self.started_at
                    + timedelta(
                        seconds=60 if same_time else index + 60
                    )
                ),
            )
            for index in range(count)
        ]

        return TripLocation.objects.bulk_create(points)

    def read_next_page(self, address):
        parsed = urlsplit(address)
        local_address = parsed.path

        if parsed.query:
            local_address += f"?{parsed.query}"

        return self.client.get(local_address)

    def test_empty_trip_returns_empty_results(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertNotIn("count", response.data)

    def test_assigned_driver_can_read_points(self):
        self.create_points(2)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(
            response["Cache-Control"],
            "private, no-store",
        )

    def test_manager_and_administrator_can_read(self):
        self.create_points(1)

        for user in (self.manager, self.administrator):
            with self.subTest(user=user.username):
                self.client.force_authenticate(user=user)

                response = self.client.get(self.url)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    len(response.data["results"]),
                    1,
                )

    def test_anonymous_user_cannot_read(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_other_driver_cannot_read(self):
        self.client.force_authenticate(user=self.other_driver)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)

    def test_points_are_ordered_by_capture_time(self):
        later = self.create_points(1)[0]
        later.recorded_at = self.started_at + timedelta(minutes=5)
        later.save(update_fields=["recorded_at"])

        earlier = self.create_points(1)[0]

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [
                point["id"]
                for point in response.data["results"]
            ],
            [earlier.pk, later.pk],
        )

    def test_cursor_returns_all_points_without_duplicates(self):
        self.create_points(501)

        expected_ids = list(
            self.trip.locations.order_by(
                "recorded_at",
                "id",
            ).values_list("id", flat=True)
        )

        first = self.client.get(self.url)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(first.data["results"]), 500)
        self.assertIsNotNone(first.data["next"])

        second = self.read_next_page(first.data["next"])

        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(second.data["results"]), 1)
        self.assertIsNone(second.data["next"])

        received_ids = [
            point["id"]
            for point in (
                first.data["results"]
                + second.data["results"]
            )
        ]

        self.assertEqual(received_ids, expected_ids)
        self.assertEqual(
            len(received_ids),
            len(set(received_ids)),
        )

    def test_same_timestamp_can_cross_page_boundary(self):
        self.create_points(501, same_time=True)

        expected_ids = list(
            self.trip.locations.order_by(
                "recorded_at",
                "id",
            ).values_list("id", flat=True)
        )

        first = self.client.get(self.url)

        self.assertEqual(first.status_code, 200)
        self.assertIsNotNone(first.data["next"])

        second = self.read_next_page(first.data["next"])

        self.assertEqual(second.status_code, 200)

        received_ids = [
            point["id"]
            for point in (
                first.data["results"]
                + second.data["results"]
            )
        ]

        self.assertEqual(received_ids, expected_ids)
        self.assertIsNone(second.data["next"])