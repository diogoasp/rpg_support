from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class AuthenticationTests(TestCase):
    def test_valid_credentials_authenticate_user(self) -> None:
        user = User.objects.create_user(
            username="nami", password="weather-map", role=User.Role.PLAYER
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": user.username, "password": "weather-map"},
        )
        self.assertRedirects(response, reverse("dashboard:home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_logout_requires_post_and_ends_session(self) -> None:
        user = User.objects.create_user(
            username="robin", password="history-book", role=User.Role.PLAYER
        )
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)
