from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from campaigns.models import Campaign
from characters.models import Character


class PermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.master = User.objects.create_user(
            username="master", password="test-pass", role=User.Role.MASTER
        )
        cls.other_master = User.objects.create_user(
            username="other", password="test-pass", role=User.Role.MASTER
        )
        cls.player = User.objects.create_user(
            username="player", password="test-pass", role=User.Role.PLAYER
        )
        cls.outsider = User.objects.create_user(
            username="outsider", password="test-pass", role=User.Role.PLAYER
        )
        cls.campaign = Campaign.objects.create(
            name="Mar Aberto", slug="mar-aberto", master=cls.master
        )
        cls.campaign.players.add(cls.player)

    def test_anonymous_user_is_redirected_to_login(self) -> None:
        response = self.client.get(reverse("dashboard:home"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next=/")

    def test_master_is_sent_to_master_dashboard(self) -> None:
        self.client.force_login(self.master)
        response = self.client.get(reverse("dashboard:home"))
        self.assertRedirects(response, reverse("dashboard:master"))

    def test_player_is_sent_to_player_dashboard(self) -> None:
        self.client.force_login(self.player)
        response = self.client.get(reverse("dashboard:home"))
        self.assertRedirects(response, reverse("dashboard:player"))

    def test_player_cannot_access_master_dashboard(self) -> None:
        self.client.force_login(self.player)
        response = self.client.get(reverse("dashboard:master"))
        self.assertEqual(response.status_code, 403)

    def test_master_cannot_access_player_dashboard(self) -> None:
        self.client.force_login(self.master)
        response = self.client.get(reverse("dashboard:player"))
        self.assertEqual(response.status_code, 403)

    def test_campaign_member_can_view_campaign(self) -> None:
        for user in (self.master, self.player):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get(self.campaign.get_absolute_url())
                self.assertEqual(response.status_code, 200)

    def test_user_from_another_campaign_cannot_view_campaign(self) -> None:
        for user in (self.other_master, self.outsider):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get(self.campaign.get_absolute_url())
                self.assertEqual(response.status_code, 403)

    def test_player_cannot_create_campaign(self) -> None:
        self.client.force_login(self.player)
        response = self.client.get(reverse("campaigns:create"))
        self.assertEqual(response.status_code, 403)

    def test_only_campaign_master_can_edit_campaign(self) -> None:
        url = reverse("campaigns:update", kwargs={"slug": self.campaign.slug})
        for user in (self.player, self.other_master):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.master)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_master_can_create_campaign_and_associate_player(self) -> None:
        self.client.force_login(self.master)
        response = self.client.post(
            reverse("campaigns:create"),
            {
                "name": "Novo Mundo",
                "slug": "novo-mundo",
                "description": "Uma nova jornada.",
                "players": [self.outsider.pk],
                "is_active": "on",
            },
        )
        campaign = Campaign.objects.get(slug="novo-mundo")
        self.assertRedirects(response, campaign.get_absolute_url())
        self.assertEqual(campaign.master, self.master)
        self.assertQuerySetEqual(campaign.players.all(), [self.outsider])

    def test_master_dashboard_shows_character_quick_actions(self) -> None:
        character = Character.objects.create(
            campaign=self.campaign,
            user=self.player,
            name="Lina",
            max_hp=20,
            current_hp=18,
            max_power_points=6,
            current_power_points=4,
            armor_class=13,
            portrait="characters/portraits/lina.png",
        )
        self.client.force_login(self.master)

        response = self.client.get(reverse("dashboard:master"))

        self.assertContains(response, "Personagens da campanha")
        self.assertContains(response, "Lina")
        self.assertContains(response, 'src="/media/characters/portraits/lina.png"')
        self.assertContains(response, "18/20")
        self.assertContains(response, reverse("characters:damage", kwargs={"pk": character.pk}))
        self.assertContains(response, reverse("characters:heal", kwargs={"pk": character.pk}))
        self.assertContains(response, reverse("inventory:add", kwargs={"pk": character.pk}))

    def test_master_dashboard_character_damage_and_heal_update_card(self) -> None:
        character = Character.objects.create(campaign=self.campaign, user=self.player, name="Lina", max_hp=20, current_hp=18)
        self.client.force_login(self.master)

        response = self.client.post(reverse("characters:damage", kwargs={"pk": character.pk}), {"amount": 7})
        self.assertContains(response, "11/20")
        character.refresh_from_db()
        self.assertEqual(character.current_hp, 11)

        response = self.client.post(reverse("characters:heal", kwargs={"pk": character.pk}), {"amount": 5})
        self.assertContains(response, "16/20")
        character.refresh_from_db()
        self.assertEqual(character.current_hp, 16)

        self.client.force_login(self.other_master)
        self.assertEqual(self.client.post(reverse("characters:damage", kwargs={"pk": character.pk}), {"amount": 1}).status_code, 404)
