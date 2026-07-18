from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from campaigns.models import Campaign
from characters.models import Character, CharacterCreation


def character_payload(name="Lina"):
    return {
        "name": name,
        "level": 1,
        "species": "Humano",
        "profession": "Navegador",
        "combat_style": "Lâminas",
        "background": "",
        "bounty": 0,
        "armor_class": 10,
        "proficiency_bonus": 2,
        "initiative": 0,
        "movement": 9,
        "max_hp": 10,
        "current_hp": 10,
        "max_power_points": 0,
        "current_power_points": 0,
        "strength": 10,
        "dexterity": 10,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10,
        "devil_fruit_name": "",
        "appearance": "",
        "personality": "",
        "dream": "",
        "notes": "",
    }


class PlayerCampaignFlowTests(TestCase):
    def setUp(self):
        self.master = User.objects.create_user("m", role=User.Role.MASTER)
        self.player = User.objects.create_user("p", password="test-pass", role=User.Role.PLAYER)
        self.outsider = User.objects.create_user("o", role=User.Role.PLAYER)
        self.c1 = Campaign.objects.create(name="Mar Aberto", slug="mar-aberto", master=self.master)
        self.c2 = Campaign.objects.create(name="Novo Mundo", slug="novo-mundo", master=self.master)
        self.c3 = Campaign.objects.create(name="Outra Mesa", slug="outra-mesa", master=self.master)
        self.c1.players.add(self.player)
        self.c2.players.add(self.player)
        self.c3.players.add(self.outsider)
        Character.objects.create(campaign=self.c1, user=self.player, **character_payload("Nami"))

    def test_login_player_lands_on_campaign_selection(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.player.username, "password": "test-pass"},
            follow=True,
        )
        self.assertContains(response, "Selecione uma campanha")
        self.assertContains(response, "Mar Aberto")
        self.assertContains(response, "Novo Mundo")
        self.assertContains(response, reverse("characters:dashboard", kwargs={"slug": self.c1.slug}))
        self.assertContains(response, reverse("characters:create", kwargs={"slug": self.c2.slug}))

    def test_player_dashboard_shows_continue_creation_for_draft(self):
        CharacterCreation.objects.create(campaign=self.c2, user=self.player, name="Usopp", current_step="review")
        self.client.force_login(self.player)
        response = self.client.get(reverse("dashboard:player"))
        self.assertContains(response, "Continuar criação")
        self.assertContains(response, f'{reverse("characters:create", kwargs={"slug": self.c2.slug})}?step=review')

    def test_player_can_create_character_for_selected_campaign(self):
        self.client.force_login(self.player)
        response = self.client.post(
            reverse("characters:create", kwargs={"slug": self.c2.slug}),
            {"step": "concept", "name": "Usopp", "concept": "Atirador curioso"},
        )
        self.assertRedirects(response, f'{reverse("characters:create", kwargs={"slug": self.c2.slug})}?step=species')
        self.assertFalse(Character.objects.filter(campaign=self.c2, user=self.player, name="Usopp").exists())
        self.assertTrue(CharacterCreation.objects.filter(campaign=self.c2, user=self.player, name="Usopp").exists())

    def test_player_cannot_create_character_for_unrelated_campaign(self):
        self.client.force_login(self.player)
        response = self.client.get(reverse("characters:create", kwargs={"slug": self.c3.slug}))
        self.assertEqual(response.status_code, 404)

    def test_master_cannot_use_player_character_creation(self):
        self.client.force_login(self.master)
        response = self.client.get(reverse("characters:create", kwargs={"slug": self.c1.slug}))
        self.assertEqual(response.status_code, 403)

    def test_character_menu_lists_existing_characters_and_drafts(self):
        CharacterCreation.objects.create(campaign=self.c2, user=self.player, name="Usopp", current_step="attributes")
        self.client.force_login(self.player)
        response = self.client.get(reverse("characters:legacy_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Personagens e criações")
        self.assertContains(response, "Nami")
        self.assertContains(response, "Ficha completa")
        self.assertContains(response, "Usopp")
        self.assertContains(response, "Atributos")
        self.assertContains(response, "Continuar criação")
