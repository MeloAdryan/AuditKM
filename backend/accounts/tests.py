from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APITestCase

class AuthenticationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(username="motorista", password="SenhaDeTeste!982")

    def login(self):
        return self.client.post(reverse("login"), {"username": "motorista", "password": "SenhaDeTeste!982"})

    def test_health_is_public(self):
        self.assertEqual(self.client.get(reverse("health")).data["status"], "ok")

    def test_profile_requires_authentication(self):
        self.assertEqual(self.client.get(reverse("me")).status_code, 401)

    def test_login_and_profile_do_not_expose_password(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + response.data["access"])
        profile = self.client.get(reverse("me"))
        self.assertEqual(profile.data["username"], "motorista")
        self.assertEqual(profile.data["role"], "DRIVER")
        self.assertNotIn("password", profile.data)

    def test_wrong_password_is_rejected(self):
        response = self.client.post(reverse("login"), {"username": "motorista", "password": "errada"})
        self.assertEqual(response.status_code, 401)

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.login().status_code, 401)

    def test_refresh_rotates_and_rejects_old_token(self):
        old = self.login().data["refresh"]
        response = self.client.post(reverse("refresh"), {"refresh": old})
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data["refresh"], old)
        self.assertEqual(self.client.post(reverse("refresh"), {"refresh": old}).status_code, 401)

    def test_logout_revokes_refresh(self):
        tokens = self.login().data
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + tokens["access"])
        self.assertEqual(self.client.post(reverse("logout"), {"refresh": tokens["refresh"]}).status_code, 200)
        self.assertEqual(self.client.post(reverse("refresh"), {"refresh": tokens["refresh"]}).status_code, 401)

    def test_profile_cannot_change_role(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.login().data["access"])
        self.assertEqual(self.client.patch(reverse("me"), {"role": "ADMIN"}).status_code, 405)
