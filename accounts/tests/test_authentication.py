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
        self.assertRedirects(response, reverse("dashboard:home"), fetch_redirect_response=False)
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

    def test_player_required_to_change_password_is_redirected_after_login(self) -> None:
        user = User.objects.create_user(
            username="usopp",
            password="shared-password",
            role=User.Role.PLAYER,
            password_change_required=True,
        )

        response = self.client.post(
            reverse("accounts:login"),
            {"username": user.username, "password": "shared-password"},
        )

        self.assertRedirects(response, reverse("accounts:force_password_change"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_required_password_change_blocks_other_pages(self) -> None:
        user = User.objects.create_user(
            username="chopper",
            password="shared-password",
            role=User.Role.PLAYER,
            password_change_required=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard:home"))

        self.assertRedirects(response, reverse("accounts:force_password_change"), fetch_redirect_response=False)

    def test_required_password_change_rejects_same_password(self) -> None:
        user = User.objects.create_user(
            username="franky",
            password="shared-password",
            role=User.Role.PLAYER,
            password_change_required=True,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:force_password_change"),
            {
                "old_password": "shared-password",
                "new_password1": "shared-password",
                "new_password2": "shared-password",
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertContains(response, "A nova senha deve ser diferente da senha atual.", status_code=422)
        user.refresh_from_db()
        self.assertTrue(user.password_change_required)

    def test_required_password_change_updates_password_once_and_keeps_session(self) -> None:
        user = User.objects.create_user(
            username="brook",
            password="shared-password",
            role=User.Role.PLAYER,
            password_change_required=True,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:force_password_change"),
            {
                "old_password": "shared-password",
                "new_password1": "individual-password-49",
                "new_password2": "individual-password-49",
            },
        )

        self.assertRedirects(response, reverse("dashboard:home"), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        user.refresh_from_db()
        self.assertFalse(user.password_change_required)
        self.assertTrue(user.check_password("individual-password-49"))

    def test_user_without_required_password_change_cannot_use_forced_page(self) -> None:
        user = User.objects.create_user(
            username="jinbe", password="fishman-karate", role=User.Role.PLAYER
        )
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:force_password_change"))

        self.assertRedirects(response, reverse("dashboard:home"), fetch_redirect_response=False)
