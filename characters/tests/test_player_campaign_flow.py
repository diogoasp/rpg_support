from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from campaigns.models import Campaign
from characters.models import (
    Character,
    CharacterCreation,
    CharacterSkill,
    CharacterTechnique,
    CharacterWeapon,
    Skill,
)
from inventory.models import InventoryItem
from ships.models import Ship


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

    def test_master_damage_and_heal_character_actions_update_card_and_close_modal(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        self.client.force_login(self.master)

        response = self.client.post(reverse("characters:damage", args=[character.pk]), {"amount": 3}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["HX-Trigger"], "modal:close")
        self.assertContains(response, "7/10")
        character.refresh_from_db()
        self.assertEqual(character.current_hp, 7)

        response = self.client.post(reverse("characters:heal", args=[character.pk]), {"amount": 2}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["HX-Trigger"], "modal:close")
        self.assertContains(response, "9/10")
        character.refresh_from_db()
        self.assertEqual(character.current_hp, 9)

    def test_master_hp_actions_do_not_revalidate_missing_portrait_file(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.portrait = "characters/portraits/missing-local-file.png"
        character.current_hp = 5
        character.save(update_fields=["portrait", "current_hp"])
        self.client.force_login(self.master)

        response = self.client.post(reverse("characters:heal", args=[character.pk]), {"amount": 2}, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["HX-Trigger"], "modal:close")
        self.assertContains(response, "7/10")
        character.refresh_from_db()
        self.assertEqual(character.current_hp, 7)

    def test_master_character_hp_action_validation_stays_in_modal(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        self.client.force_login(self.master)

        response = self.client.post(reverse("characters:damage", args=[character.pk]), {"amount": ""}, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.headers["HX-Retarget"], "#modal-content")
        self.assertEqual(response.headers["HX-Reswap"], "innerHTML")

    def test_player_character_dashboard_has_collapsible_play_sections(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        InventoryItem.objects.create(character=character, name="Log Pose", description="Aponta para a próxima ilha.", quantity=1)
        Ship.objects.create(campaign=self.c1, name="Going Merry", max_hp=100, current_hp=80, max_crew=8, current_crew=5, speed="8 nós", cannons=2, facilities="Cozinha", belongs_to_crew=True)

        self.client.force_login(self.player)
        response = self.client.get(reverse("characters:dashboard", kwargs={"slug": self.c1.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<details", count=3)
        self.assertContains(response, "Ficha de jogo")
        self.assertContains(response, "Abrir ficha completa")
        self.assertContains(response, reverse("characters:sheet", kwargs={"slug": self.c1.slug}))
        self.assertContains(response, "Inventário")
        self.assertContains(response, "Log Pose")
        self.assertContains(response, "Navio")
        self.assertContains(response, "Going Merry")

    def test_character_sheet_uses_final_visual_layout_with_character_data(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.age = "20"
        character.height = "1,70 m"
        character.weight = "58 kg"
        character.dream_path = "knowledge_companionship"
        character.save()
        InventoryItem.objects.create(character=character, name="Clima-Tact", description="Bastão climático.", quantity=1)

        self.client.force_login(self.player)
        response = self.client.get(reverse("characters:sheet", kwargs={"slug": self.c1.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "op-sheet")
        self.assertContains(response, "Ficha de Personagem")
        self.assertContains(response, "Nami")
        self.assertContains(response, "Atributos e Status Vitais")
        self.assertContains(response, "Vontade (VON)")
        self.assertContains(response, "Presença (PRE)")
        self.assertContains(response, "20")
        self.assertContains(response, "1,70 m")
        self.assertContains(response, "58 kg")
        self.assertContains(response, "Conhecimento pelo Companheirismo")
        self.assertContains(response, "Clima-Tact")
        self.assertNotContains(response, "Inteligência")
        self.assertNotContains(response, "Carisma")

    def test_player_can_update_subjective_sheet_fields(self):
        self.client.force_login(self.player)
        response = self.client.get(reverse("characters:sheet", kwargs={"slug": self.c1.slug}))
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, "Retrato/ilustração")

        response = self.client.post(
            reverse("characters:sheet", kwargs={"slug": self.c1.slug}),
            {
                "age": "21",
                "height": "1,68 m",
                "weight": "55 kg",
                "dream_path": "freedom_strength",
                "appearance": "Cabelos alaranjados e olhar atento.",
                "personality": "Calculista e protetora.",
                "dream": "Mapear todos os mares.",
                "notes": "História atualizada pela ficha completa.",
            },
            follow=True,
        )

        self.assertContains(response, "Ficha narrativa atualizada.")
        character = Character.objects.get(campaign=self.c1, user=self.player)
        self.assertEqual(character.age, "21")
        self.assertEqual(character.height, "1,68 m")
        self.assertEqual(character.weight, "55 kg")
        self.assertEqual(character.dream_path, "freedom_strength")
        self.assertEqual(character.dream, "Mapear todos os mares.")
        self.assertEqual(character.notes, "História atualizada pela ficha completa.")
        self.assertContains(response, "Mapear todos os mares.")

    def test_print_sheet_lists_all_skills_and_combat_without_inventory(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.strength = 14
        character.dexterity = 12
        character.proficiency_bonus = 2
        character.age = "20"
        character.height = "1,70 m"
        character.background = "Marinheiro"
        character.save()
        acrobacia = Skill.objects.create(name="Acrobacia", slug="acrobacia", related_attribute="dexterity", sort_order=2)
        atletismo = Skill.objects.create(name="Atletismo", slug="atletismo", related_attribute="strength", sort_order=1)
        sobrevivencia = Skill.objects.create(name="Sobrevivência", slug="sobrevivencia", related_attribute="wisdom", sort_order=3)
        CharacterSkill.objects.create(character=character, skill=atletismo, is_proficient=True)
        CharacterWeapon.objects.create(
            character=character,
            name="Pistola",
            range_text="18 m",
            damage_die="1d8",
            attribute_modifier="dexterity",
            weapon_type="Arma de Fogo",
            is_proficient=True,
        )
        CharacterTechnique.objects.create(
            character=character,
            name="Corte do Vento",
            description="Um corte rápido.",
            range_text="3 m",
            damage_die="1d6",
            damage_text="1d6+2 de dano Cortante",
            attribute_modifier="strength",
            required_weapon_type="Arma de Fogo",
            power_points_cost=1,
            category=CharacterTechnique.Category.ATTACK,
            technique_type=CharacterTechnique.TechniqueType.COMBAT,
        )
        CharacterTechnique.objects.create(
            character=character,
            name="Canção de Coragem",
            description="Inspira um aliado.",
            range_text="9 m",
            damage_die="1d6",
            attribute_modifier="presence",
            power_points_cost=2,
            category=CharacterTechnique.Category.SUPPORT,
            technique_type=CharacterTechnique.TechniqueType.BUFF,
        )
        CharacterTechnique.objects.create(
            character=character,
            name="Punho Meteoro",
            description="Golpe desarmado especial.",
            range_text="corpo a corpo",
            damage_die="1d6",
            category=CharacterTechnique.Category.ATTACK,
            technique_type=CharacterTechnique.TechniqueType.UNARMED,
        )
        InventoryItem.objects.create(character=character, name="Clima-Tact", description="Não deve sair na impressão.", quantity=1)

        self.client.force_login(self.player)
        response = self.client.get(reverse("characters:print", kwargs={"slug": self.c1.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ficha impressa de Nami")
        self.assertContains(response, "Antecedência")
        self.assertContains(response, "Atributos e Sobrevivência")
        self.assertContains(response, "Testes e Perícias")
        self.assertContains(response, "Acrobacia")
        self.assertContains(response, "Atletismo")
        self.assertContains(response, "Sobrevivência")
        self.assertContains(response, "Descrição")
        self.assertContains(response, "Saltar obstáculos, manter equilíbrio e executar manobras corporais.")
        self.assertContains(response, "<td>Atletismo</td><td>Força física para correr, nadar, escalar, empurrar ou agarrar.</td><td>Força</td><td>Sim</td><td>+4</td>", html=True)
        self.assertContains(response, "<td>Acrobacia</td><td>Saltar obstáculos, manter equilíbrio e executar manobras corporais.</td><td>Destreza</td><td>Não</td><td>+1</td>", html=True)
        self.assertLess(response.content.index(b"Acrobacia"), response.content.index(b"Atletismo"))
        self.assertContains(response, "Ataques possíveis")
        self.assertContains(response, "Pistola")
        self.assertContains(response, "Ataque básico: Pistola")
        self.assertContains(response, "1d8 +1")
        self.assertContains(response, "Teste de ataque")
        self.assertContains(response, "1d20 +3")
        self.assertContains(response, "Proficiência: sim")
        self.assertContains(response, "Corte do Vento")
        self.assertContains(response, "Técnica com arma")
        self.assertContains(response, "1d20 +4")
        self.assertContains(response, "1d6 + 1d8 +2")
        self.assertContains(response, "Canção de Coragem")
        self.assertContains(response, "1d20 +0")
        self.assertContains(response, "(1d6 +0) / 2")
        self.assertContains(response, "Punho Meteoro")
        self.assertContains(response, "1d6 + 1d4 +2")
        self.assertContains(response, "O resultado dividido por 2")
        self.assertNotContains(response, "Inventário")
        self.assertNotContains(response, "Clima-Tact")

    def test_technique_category_limits_available_types(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        technique = CharacterTechnique(
            character=character,
            name="Cura inválida",
            category=CharacterTechnique.Category.SUPPORT,
            technique_type=CharacterTechnique.TechniqueType.COMBAT,
            required_weapon_type="Arma de Fogo",
        )

        with self.assertRaises(ValidationError):
            technique.full_clean()

        technique.category = CharacterTechnique.Category.ATTACK
        technique.technique_type = CharacterTechnique.TechniqueType.COMBAT
        technique.required_weapon_type = ""
        with self.assertRaises(ValidationError):
            technique.full_clean()

    def test_print_sheet_keeps_player_campaign_isolation(self):
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("characters:print", kwargs={"slug": self.c1.slug}))
        self.assertEqual(response.status_code, 404)
