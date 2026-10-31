from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User
from .models import Vehicle


class VehicleAPITests(APITestCase):
    def setUp(self):
        self.driver = User.objects.create_user(
            username="motorista_teste",
            password="SenhaTeste!982",
            role=User.Role.DRIVER,
        )

        self.manager = User.objects.create_user(
            username="gestor_teste",
            password="SenhaTeste!982",
            role=User.Role.MANAGER,
        )

        self.administrator = User.objects.create_user(
            username="admin_teste",
            password="SenhaTeste!982",
            role=User.Role.ADMIN,
        )

        self.vehicle = Vehicle.objects.create(
            plate="ABC1D23",
            brand="Fiat",
            model="Strada",
            year=2024,
            current_km=15000,
        )

        self.list_url = reverse("vehicle-list")
        self.detail_url = reverse(
            "vehicle-detail",
            args=[self.vehicle.pk],
        )

        self.payload = {
            "plate": "DEF4G56",
            "brand": "Toyota",
            "model": "Hilux",
            "year": 2024,
            "current_km": 20000,
            "status": "ACTIVE",
        }

    def test_anonymous_user_cannot_list(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 401)

    def test_driver_can_list(self):
        self.client.force_authenticate(user=self.driver)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["plate"],
            "ABC1D23",
        )

    def test_driver_cannot_create_or_update(self):
        self.client.force_authenticate(user=self.driver)

        create_response = self.client.post(
            self.list_url,
            self.payload,
            format="json",
        )

        update_response = self.client.patch(
            self.detail_url,
            {"status": "INACTIVE"},
            format="json",
        )

        self.assertEqual(create_response.status_code, 403)
        self.assertEqual(update_response.status_code, 403)

        self.vehicle.refresh_from_db()

        self.assertEqual(self.vehicle.status, Vehicle.Status.ACTIVE)
        self.assertEqual(Vehicle.objects.count(), 1)

    def test_manager_and_administrator_can_create_and_update(self):
        for index, user in enumerate(
            [self.manager, self.administrator]
        ):
            with self.subTest(role=user.role):
                self.client.force_authenticate(user=user)

                payload = {
                    **self.payload,
                    "plate": f"DEF{index}G56",
                }

                response = self.client.post(
                    self.list_url,
                    payload,
                    format="json",
                )

                self.assertEqual(response.status_code, 201)

                detail_url = reverse(
                    "vehicle-detail",
                    args=[response.data["id"]],
                )

                update_response = self.client.patch(
                    detail_url,
                    {"status": "MAINTENANCE"},
                    format="json",
                )

                self.assertEqual(update_response.status_code, 200)

                vehicle = Vehicle.objects.get(pk=response.data["id"])

                self.assertEqual(
                    vehicle.status,
                    Vehicle.Status.MAINTENANCE,
                )

    def test_duplicate_plate_is_rejected(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            self.list_url,
            {**self.payload, "plate": self.vehicle.plate},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("plate", response.data)

    def test_invalid_plate_is_rejected(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            self.list_url,
            {**self.payload, "plate": "123"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("plate", response.data)

    def test_odometer_cannot_be_changed_by_cadastral_update(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.patch(
            self.detail_url,
            {"current_km": 10000},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.vehicle.refresh_from_db()

        self.assertEqual(self.vehicle.current_km, 15000)

    def test_delete_is_not_available(self):
        self.client.force_authenticate(user=self.administrator)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, 405)
        self.assertTrue(
            Vehicle.objects.filter(pk=self.vehicle.pk).exists()
        )