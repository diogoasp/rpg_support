from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from campaigns.models import Campaign
from characters.models import (
    Character,
    CharacterChangeLog,
    CharacterCondition,
    CharacterCreation,
    CharacterFeature,
    CharacterRecordSource,
    CharacterSkill,
    CharacterTechnique,
    CharacterTechniqueActivation,
    CharacterTechniqueGrade,
    CharacterTechniqueUse,
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
        self.other_master = User.objects.create_user("m2", role=User.Role.MASTER)
        self.player = User.objects.create_user("p", password="test-pass", role=User.Role.PLAYER)
        self.outsider = User.objects.create_user("o", role=User.Role.PLAYER)
        self.c1 = Campaign.objects.create(name="Mar Aberto", slug="mar-aberto", master=self.master)
        self.c2 = Campaign.objects.create(name="Novo Mundo", slug="novo-mundo", master=self.master)
        self.c3 = Campaign.objects.create(name="Outra Mesa", slug="outra-mesa", master=self.other_master)
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
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.portrait = "characters/portraits/nami.png"
        character.save(update_fields=["portrait"])
        CharacterCreation.objects.create(campaign=self.c2, user=self.player, name="Usopp", current_step="attributes")
        self.client.force_login(self.player)
        response = self.client.get(reverse("characters:legacy_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Personagens e criações")
        self.assertContains(response, "Nami")
        self.assertContains(response, 'src="/media/characters/portraits/nami.png"')
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

    def test_master_character_list_cards_show_portrait(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.portrait = "characters/portraits/nami.png"
        character.save(update_fields=["portrait"])
        self.client.force_login(self.master)

        response = self.client.get(reverse("characters:master_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Personagens das minhas campanhas")
        self.assertContains(response, character.name)
        self.assertContains(response, 'src="/media/characters/portraits/nami.png"')
        self.assertContains(response, reverse("characters:master_sheet", args=[character.pk]))

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
        CharacterFeature.objects.create(character=character, name="Navegação precisa", source="Antecedente", description="Lê correntes marítimas.")
        CharacterFeature.objects.create(character=character, name="Medo do escuro", source="Defeito", description="Hesita em locais sem luz.")

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
        self.assertContains(response, "Navegação precisa")
        self.assertContains(response, "Medo do escuro")
        self.assertLess(response.content.index(b"Tra\xc3\xa7os e Vantagens"), response.content.index(b"Navega\xc3\xa7\xc3\xa3o precisa"))
        self.assertLess(response.content.index(b"Condi\xc3\xa7\xc3\xb5es e Limita\xc3\xa7\xc3\xb5es"), response.content.index(b"Medo do escuro"))
        self.assertNotContains(response, "Inteligência")
        self.assertNotContains(response, "Carisma")

    def test_campaign_master_can_access_player_full_sheet_read_only(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        self.client.force_login(self.master)

        response = self.client.get(reverse("characters:master_sheet", args=[character.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "op-sheet")
        self.assertContains(response, character.name)
        self.assertContains(response, "Voltar à ficha do mestre")
        self.assertContains(response, reverse("characters:edit", args=[character.pk]))
        self.assertNotContains(response, "Salvar alterações")

    def test_other_master_cannot_access_player_full_sheet(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        self.client.force_login(self.other_master)

        response = self.client.get(reverse("characters:master_sheet", args=[character.pk]))

        self.assertEqual(response.status_code, 404)

    def test_master_cannot_post_player_sheet_edits(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        self.client.force_login(self.master)

        response = self.client.post(
            reverse("characters:master_sheet", args=[character.pk]),
            {"age": "99", "height": "", "weight": "", "dream_path": "", "dream": "", "appearance": "", "personality": "", "notes": ""},
        )

        self.assertEqual(response.status_code, 404)
        character.refresh_from_db()
        self.assertNotEqual(character.age, "99")

    def test_campaign_master_does_not_use_player_slug_sheet_route(self):
        self.client.force_login(self.master)

        response = self.client.get(reverse("characters:sheet", kwargs={"slug": self.c1.slug}))

        self.assertEqual(response.status_code, 404)

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
        CharacterFeature.objects.create(character=character, name="Olhos de navegador", source="Antecedente", description="Percebe mudanças no clima.")
        CharacterFeature.objects.create(character=character, name="Orgulho ferido", source="Defeito", description="Não aceita insultos facilmente.")
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
        self.assertContains(response, "Personalidade, Singularidades e Limitações")
        self.assertContains(response, "Traços e Vantagens")
        self.assertContains(response, "Condições e Limitações")
        self.assertContains(response, "Olhos de navegador")
        self.assertContains(response, "Orgulho ferido")
        self.assertLess(response.content.index(b"Tra\xc3\xa7os e Vantagens"), response.content.index(b"Olhos de navegador"))
        self.assertLess(response.content.index(b"Condi\xc3\xa7\xc3\xb5es e Limita\xc3\xa7\xc3\xb5es"), response.content.index(b"Orgulho ferido"))
        self.assertNotContains(response, "Inventário")
        self.assertNotContains(response, "Clima-Tact")

    def test_print_sheet_hides_buff_calculation_when_buff_has_no_die(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        CharacterTechnique.objects.create(
            character=character,
            name="Shinsoku Hakujaku",
            description="Você se move rapidamente, com passos firmes.",
            range_text="-",
            damage_die="",
            damage_text="",
            attribute_modifier="strength",
            power_points_cost=2,
            category=CharacterTechnique.Category.SUPPORT,
            technique_type=CharacterTechnique.TechniqueType.BUFF,
        )

        self.client.force_login(self.player)
        response = self.client.get(reverse("characters:print", kwargs={"slug": self.c1.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shinsoku Hakujaku")
        self.assertContains(response, "1d20 +0")
        self.assertContains(response, "<span><strong>Atributo</strong><br>Força</span>", html=True)
        self.assertContains(response, "<span><strong>Alcance</strong><br>-</span>", html=True)
        self.assertNotContains(response, "<span><strong>Dado</strong><br>Conforme descrição</span>", html=True)
        self.assertNotContains(response, "<span><strong>Buff</strong><br>(Conforme descrição +0) / 2</span>", html=True)

    def test_print_sheet_describes_continuous_and_graded_techniques(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        CharacterTechnique.objects.create(
            character=character,
            name="Postura Glacial",
            usage_mode=CharacterTechnique.UsageMode.CONTINUOUS,
            power_points_cost=2,
            effect_summary="1d8 nos ataques e 1d8 de redução de dano",
        )
        graded = CharacterTechnique.objects.create(
            character=character,
            name="Hit Me With Your Best Shot",
            usage_mode=CharacterTechnique.UsageMode.GRADED,
            category=CharacterTechnique.Category.SUPPORT,
            technique_type=CharacterTechnique.TechniqueType.HEAL,
        )
        CharacterTechniqueGrade.objects.bulk_create([
            CharacterTechniqueGrade(technique=graded, grade=0, effect_summary="Cura 50% do ataque básico"),
            CharacterTechniqueGrade(technique=graded, grade=1, effect_summary="Cura 100% do ataque básico"),
            CharacterTechniqueGrade(technique=graded, grade=2, effect_summary="Cura 200% e concede vantagem"),
        ])
        self.client.force_login(self.player)

        response = self.client.get(reverse("characters:print", kwargs={"slug": self.c1.slug}))

        self.assertContains(response, "Efeito contínuo")
        self.assertContains(response, "2 para ativar; 1 por rodada")
        self.assertContains(response, "1d8 nos ataques e 1d8 de redução de dano")
        self.assertContains(response, "Grau 0 (0 PP):")
        self.assertContains(response, "Cura 50% do ataque básico")
        self.assertContains(response, "Grau 2 (2 PP):")
        self.assertContains(response, "Cura 200% e concede vantagem")

    def test_print_sheet_base_unarmed_attack_uses_only_unarmed_level_die(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.strength = 14
        character.save(update_fields=["strength"])
        CharacterTechnique.objects.create(
            character=character,
            name="Ataque Desarmado",
            description="Ataque desarmado padrão.",
            range_text="1m",
            damage_die="",
            damage_text="1d4 + Modificador de Força",
            category=CharacterTechnique.Category.ATTACK,
            technique_type=CharacterTechnique.TechniqueType.UNARMED,
        )

        self.client.force_login(self.player)
        response = self.client.get(reverse("characters:print", kwargs={"slug": self.c1.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ataque Desarmado")
        self.assertContains(response, "<span><strong>Dado</strong><br>1d4</span>", html=True)
        self.assertContains(response, "<span><strong>Dano</strong><br>1d4 +2</span>", html=True)
        self.assertNotContains(response, "1d4 + 1d4")

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

    def test_player_can_manage_current_hp_but_not_max_hp(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        self.client.force_login(self.player)

        response = self.client.post(reverse("characters:player_damage", kwargs={"slug": self.c1.slug}), {"amount": 999}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        character.refresh_from_db()
        self.assertEqual(character.current_hp, 0)
        self.assertEqual(character.max_hp, 10)

        response = self.client.post(reverse("characters:player_heal", kwargs={"slug": self.c1.slug}), {"amount": 999, "max_hp": 999}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        character.refresh_from_db()
        self.assertEqual(character.current_hp, 10)
        self.assertEqual(character.max_hp, 10)
        self.assertTrue(CharacterChangeLog.objects.filter(character=character, action="heal", user=self.player).exists())

    def test_player_can_manage_current_power_points_but_not_maximum(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.max_power_points = 6
        character.current_power_points = 4
        character.save(update_fields=["max_power_points", "current_power_points"])
        self.client.force_login(self.player)

        response = self.client.post(reverse("characters:player_pp_spend", kwargs={"slug": self.c1.slug}), {"amount": 5, "max_power_points": 999}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        character.refresh_from_db()
        self.assertEqual(character.current_power_points, 0)
        self.assertEqual(character.max_power_points, 6)

        response = self.client.post(reverse("characters:player_pp_recover", kwargs={"slug": self.c1.slug}), {"amount": 999}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        character.refresh_from_db()
        self.assertEqual(character.current_power_points, 6)
        self.assertEqual(character.max_power_points, 6)

    def test_player_sheet_renders_mobile_first_play_surface(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        CharacterTechnique.objects.create(character=character, name="Corte Rápido", power_points_cost=2, is_featured=True)
        InventoryItem.objects.create(character=character, name="Ração", quantity=2, is_visible=True, is_active=True)
        self.client.force_login(self.player)

        response = self.client.get(reverse("characters:sheet", kwargs={"slug": self.c1.slug}))

        self.assertContains(response, 'class="op-mobile-play-shell"')
        self.assertContains(response, "Recursos")
        self.assertContains(response, "Habilidades")
        self.assertContains(response, "Itens")
        self.assertContains(response, "Descanso")
        self.assertContains(response, "- Dano")
        self.assertContains(response, "+ Recuperar")
        self.assertContains(response, "Favoritas")
        self.assertContains(response, "data-open-reference-sheet")
        self.assertEqual(response.content.count(b"- Dano"), 1)
        self.assertEqual(response.content.count(b"Corte R\xc3\xa1pido usado"), 0)

        damage_form = self.client.get(reverse("characters:player_damage", kwargs={"slug": self.c1.slug}), HTTP_HX_REQUEST="true")
        self.assertContains(damage_form, 'class="modal-body op-mobile-action-form"')
        self.assertContains(damage_form, 'inputmode="numeric"')

    def test_player_can_use_technique_and_undo_power_point_spend(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.max_power_points = 6
        character.current_power_points = 4
        character.save(update_fields=["max_power_points", "current_power_points"])
        technique = CharacterTechnique.objects.create(character=character, name="Corte Ascendente", power_points_cost=2)
        self.client.force_login(self.player)

        response = self.client.post(reverse("characters:player_technique_use", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}), HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        character.refresh_from_db()
        self.assertEqual(character.current_power_points, 2)
        self.assertContains(response, "Corte Ascendente usado")
        self.assertContains(response, "Desfazer")

        response = self.client.post(reverse("characters:player_technique_undo", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}), HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        character.refresh_from_db()
        self.assertEqual(character.current_power_points, 4)

        response = self.client.post(reverse("characters:player_technique_undo", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}), HTTP_HX_REQUEST="true")
        character.refresh_from_db()
        self.assertEqual(character.current_power_points, 4)
        self.assertContains(response, "Não há uso")

    def test_player_uses_graded_technique_with_cost_derived_from_grade(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.max_power_points = 6
        character.current_power_points = 4
        character.save(update_fields=["max_power_points", "current_power_points"])
        technique = CharacterTechnique.objects.create(character=character, name="Hit Me With Your Best Shot", usage_mode=CharacterTechnique.UsageMode.GRADED)
        CharacterTechniqueGrade.objects.bulk_create([
            CharacterTechniqueGrade(technique=technique, grade=0, effect_summary="Cura 50% do ataque básico"),
            CharacterTechniqueGrade(technique=technique, grade=1, effect_summary="Cura 100% do ataque básico"),
            CharacterTechniqueGrade(technique=technique, grade=2, effect_summary="Cura 200% e concede vantagem"),
        ])
        self.client.force_login(self.player)

        response = self.client.post(reverse("characters:player_technique_use", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}), {"grade": 2}, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        character.refresh_from_db()
        self.assertEqual(character.current_power_points, 2)
        use = CharacterTechniqueUse.objects.get(technique=technique)
        self.assertEqual((use.grade, use.power_points_spent), (2, 2))
        self.assertContains(response, "Grau 2")

    def test_graded_technique_rejects_missing_grade_and_insufficient_pp(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.max_power_points = 2
        character.current_power_points = 1
        character.save(update_fields=["max_power_points", "current_power_points"])
        technique = CharacterTechnique.objects.create(character=character, name="Técnica graduada", usage_mode=CharacterTechnique.UsageMode.GRADED)
        for grade in range(3):
            CharacterTechniqueGrade.objects.create(technique=technique, grade=grade, effect_summary=f"Efeito {grade}")
        self.client.force_login(self.player)

        missing = self.client.post(reverse("characters:player_technique_use", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}), HTTP_HX_REQUEST="true")
        insufficient = self.client.post(reverse("characters:player_technique_use", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}), {"grade": 2}, HTTP_HX_REQUEST="true")

        self.assertContains(missing, "Escolha o grau")
        self.assertContains(insufficient, "PP insuficiente")
        character.refresh_from_db()
        self.assertEqual(character.current_power_points, 1)

    def test_player_activates_maintains_and_ends_continuous_technique(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.max_power_points = 6
        character.current_power_points = 5
        character.save(update_fields=["max_power_points", "current_power_points"])
        technique = CharacterTechnique.objects.create(character=character, name="Postura Glacial", usage_mode=CharacterTechnique.UsageMode.CONTINUOUS, power_points_cost=2, effect_summary="1d8 nos ataques e 1d8 de redução")
        self.client.force_login(self.player)

        activated = self.client.post(reverse("characters:player_technique_use", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}), HTTP_HX_REQUEST="true")
        maintained = self.client.post(reverse("characters:player_technique_maintain", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}), HTTP_HX_REQUEST="true")

        self.assertContains(activated, "ativada")
        self.assertContains(maintained, "mantida")
        character.refresh_from_db()
        activation = CharacterTechniqueActivation.objects.get(technique=technique)
        self.assertEqual(character.current_power_points, 2)
        self.assertEqual(activation.rounds_maintained, 1)

        ended = self.client.post(reverse("characters:player_technique_end", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}), HTTP_HX_REQUEST="true")
        self.assertContains(ended, "encerrada")
        activation.refresh_from_db()
        self.assertEqual(activation.status, CharacterTechniqueActivation.Status.ENDED)

    def test_continuous_technique_cannot_be_activated_twice(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.max_power_points = 6
        character.current_power_points = 6
        character.save(update_fields=["max_power_points", "current_power_points"])
        technique = CharacterTechnique.objects.create(character=character, name="Postura", usage_mode=CharacterTechnique.UsageMode.CONTINUOUS, power_points_cost=2)
        self.client.force_login(self.player)
        url = reverse("characters:player_technique_use", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk})

        self.client.post(url, HTTP_HX_REQUEST="true")
        response = self.client.post(url, HTTP_HX_REQUEST="true")

        self.assertContains(response, "já está ativa")
        character.refresh_from_db()
        self.assertEqual(character.current_power_points, 4)
        self.assertEqual(CharacterTechniqueActivation.objects.filter(technique=technique, status="active").count(), 1)

    def test_player_cannot_use_technique_without_enough_power_points(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.max_power_points = 6
        character.current_power_points = 1
        character.save(update_fields=["max_power_points", "current_power_points"])
        technique = CharacterTechnique.objects.create(character=character, name="Explosão", power_points_cost=2)
        self.client.force_login(self.player)

        response = self.client.post(reverse("characters:player_technique_use", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}), HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        character.refresh_from_db()
        self.assertEqual(character.current_power_points, 1)
        self.assertContains(response, "PP insuficiente")

    def test_player_can_use_consumable_item(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        item = InventoryItem.objects.create(character=character, name="Poção", quantity=2, is_visible=True, is_active=True)
        self.client.force_login(self.player)

        response = self.client.post(reverse("inventory:use", kwargs={"pk": item.pk}), HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)
        self.assertContains(response, "Item usado: Poção")

    def test_player_rest_actions_update_current_resources(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.max_hp = 20
        character.current_hp = 3
        character.max_power_points = 6
        character.current_power_points = 1
        character.save(update_fields=["max_hp", "current_hp", "max_power_points", "current_power_points"])
        self.client.force_login(self.player)

        response = self.client.post(reverse("characters:player_short_rest", kwargs={"slug": self.c1.slug}), HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        character.refresh_from_db()
        self.assertEqual(character.current_hp, 13)
        self.assertEqual(character.current_power_points, 4)

        response = self.client.post(reverse("characters:player_long_rest", kwargs={"slug": self.c1.slug}), HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        character.refresh_from_db()
        self.assertEqual(character.current_hp, 20)
        self.assertEqual(character.current_power_points, 6)

    def test_player_can_start_great_damage_recovery(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.max_hp = 30
        character.current_hp = 12
        character.save(update_fields=["max_hp", "current_hp"])
        self.client.force_login(self.player)

        response = self.client.post(reverse("characters:player_great_damage_recovery", kwargs={"slug": self.c1.slug}), {"days": 3}, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        character.refresh_from_db()
        self.assertEqual(character.great_damage_recovery_days, 3)
        self.assertEqual(character.great_damage_recovery_day, 1)
        self.assertEqual(character.great_damage_recovery_hp_per_rest, 6)
        self.assertContains(response, "Dia 1 de 3")

    def test_other_player_cannot_use_sheet_state_routes(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        original_hp = character.current_hp
        self.client.force_login(self.outsider)

        response = self.client.post(reverse("characters:player_damage", kwargs={"slug": self.c1.slug}), {"amount": 3}, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 404)
        character.refresh_from_db()
        self.assertEqual(character.current_hp, original_hp)

    def test_player_can_create_update_duplicate_and_remove_manual_technique(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.dexterity = 18
        character.save(update_fields=["dexterity"])
        self.client.force_login(self.player)

        response = self.client.post(
            reverse("characters:player_technique_create", kwargs={"slug": self.c1.slug}),
            {
                "name": "Golpe Perfurante",
                "description": "Ataque customizado.",
                "action_type": "action",
                "range_text": "3 m",
                "damage_text": "",
                "damage_die": "2d8",
                "attribute_modifier": "dexterity",
                "required_weapon_type": "",
                "power_points_cost": 2,
                "category": CharacterTechnique.Category.ATTACK,
                "technique_type": CharacterTechnique.TechniqueType.INNATE,
                "is_available": "on",
                "sort_order": 1,
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        technique = CharacterTechnique.objects.get(character=character, name="Golpe Perfurante")
        self.assertEqual(technique.source_type, CharacterRecordSource.PLAYER)
        self.assertEqual(technique.attribute_modifier_value, 4)
        self.assertContains(response, "Destreza +4")

        response = self.client.post(
            reverse("characters:player_technique_update", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}),
            {
                "name": "Golpe Perfurante Revisado",
                "description": "Ataque customizado.",
                "action_type": "action",
                "range_text": "3 m",
                "damage_text": "",
                "damage_die": "2d8",
                "attribute_modifier": "dexterity",
                "required_weapon_type": "",
                "power_points_cost": 1,
                "category": CharacterTechnique.Category.ATTACK,
                "technique_type": CharacterTechnique.TechniqueType.INNATE,
                "is_available": "on",
                "sort_order": 1,
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        technique.refresh_from_db()
        self.assertEqual(technique.name, "Golpe Perfurante Revisado")

        response = self.client.post(reverse("characters:player_technique_duplicate", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}), HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CharacterTechnique.objects.filter(character=character, name="Golpe Perfurante Revisado (cópia)", source_type=CharacterRecordSource.PLAYER).exists())

        response = self.client.post(reverse("characters:player_technique_delete", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}), HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        technique.refresh_from_db()
        self.assertFalse(technique.is_available)

    def test_player_creates_and_duplicates_graded_technique_with_all_grades(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        self.client.force_login(self.player)
        payload = {
            "name": "Tiro Medicinal",
            "description": "Munição de cura.",
            "effect_summary": "Cura conforme o grau",
            "usage_mode": CharacterTechnique.UsageMode.GRADED,
            "action_type": "action",
            "attribute_modifier": "dexterity",
            "power_points_cost": 99,
            "category": CharacterTechnique.Category.SUPPORT,
            "technique_type": CharacterTechnique.TechniqueType.HEAL,
            "is_available": "on",
            "grade_0_effect_summary": "Cura 50%",
            "grade_0_description": "Metade do dano básico.",
            "grade_1_effect_summary": "Cura 100%",
            "grade_1_description": "Mesmo valor do dano básico.",
            "grade_2_effect_summary": "Cura 200% e vantagem",
            "grade_2_description": "Duas vezes o dano e vantagem no próximo ataque.",
        }

        response = self.client.post(reverse("characters:player_technique_create", kwargs={"slug": self.c1.slug}), payload, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        technique = CharacterTechnique.objects.get(character=character, name="Tiro Medicinal")
        self.assertEqual(technique.power_points_cost, 0)
        self.assertEqual(list(technique.grades.values_list("grade", flat=True)), [0, 1, 2])

        self.client.post(reverse("characters:player_technique_duplicate", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}), HTTP_HX_REQUEST="true")
        duplicate = CharacterTechnique.objects.get(character=character, name="Tiro Medicinal (cópia)")
        self.assertEqual(list(duplicate.grades.values_list("effect_summary", flat=True)), ["Cura 50%", "Cura 100%", "Cura 200% e vantagem"])

    def test_player_cannot_remove_system_technique(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        technique = CharacterTechnique.objects.create(character=character, name="Técnica do sistema", category=CharacterTechnique.Category.ATTACK, technique_type=CharacterTechnique.TechniqueType.INNATE, source_type=CharacterRecordSource.LEVEL_UP)
        self.client.force_login(self.player)

        response = self.client.post(reverse("characters:player_technique_delete", kwargs={"slug": self.c1.slug, "technique_pk": technique.pk}), HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 403)
        technique.refresh_from_db()
        self.assertTrue(technique.is_available)

    def test_player_can_manage_manual_weapon_without_granting_proficiency(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        self.client.force_login(self.player)

        response = self.client.post(
            reverse("characters:player_weapon_create", kwargs={"slug": self.c1.slug}),
            {"name": "Bastão", "range_text": "1 m", "damage_die": "1d6", "attribute_modifier": "strength", "weapon_type": "Simples", "is_available": "on", "is_proficient": "on", "sort_order": 0},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        weapon = CharacterWeapon.objects.get(character=character, name="Bastão")
        self.assertEqual(weapon.source_type, CharacterRecordSource.PLAYER)
        self.assertFalse(weapon.is_proficient)

        response = self.client.post(reverse("characters:player_weapon_delete", kwargs={"slug": self.c1.slug, "weapon_pk": weapon.pk}), HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        weapon.refresh_from_db()
        self.assertFalse(weapon.is_available)

    def test_player_can_manage_manual_feature_but_not_system_feature(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        system_feature = CharacterFeature.objects.create(character=character, name="Traço de espécie", source="Espécie", source_type=CharacterRecordSource.CHARACTER_CREATION)
        self.client.force_login(self.player)

        response = self.client.post(
            reverse("characters:player_feature_create", kwargs={"slug": self.c1.slug}),
            {"name": "Voto pessoal", "description": "Nunca abandona aliados.", "source": "Narrativa", "is_available": "on", "sort_order": 0},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        feature = CharacterFeature.objects.get(character=character, name="Voto pessoal")
        self.assertEqual(feature.source_type, CharacterRecordSource.PLAYER)

        response = self.client.post(reverse("characters:player_feature_delete", kwargs={"slug": self.c1.slug, "feature_pk": system_feature.pk}), HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 403)
        system_feature.refresh_from_db()
        self.assertTrue(system_feature.is_available)

    def test_player_can_add_and_remove_condition(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        self.client.force_login(self.player)

        response = self.client.post(reverse("characters:player_condition_add", kwargs={"slug": self.c1.slug}), {"name": "Sangrando", "description": "Ferimento aberto."}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        condition = CharacterCondition.objects.get(character=character, name="Sangrando")

        response = self.client.post(reverse("characters:player_condition_remove", kwargs={"slug": self.c1.slug, "condition_pk": condition.pk}), HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        condition.refresh_from_db()
        self.assertFalse(condition.is_active)

    def test_skill_bonus_remains_automatic_and_player_sheet_does_not_expose_proficiency(self):
        character = Character.objects.get(campaign=self.c1, user=self.player)
        character.strength = 16
        character.proficiency_bonus = 2
        character.save(update_fields=["strength", "proficiency_bonus"])
        atletismo = Skill.objects.create(name="Atletismo", slug="atletismo-auto", related_attribute="strength")
        character_skill = CharacterSkill.objects.create(character=character, skill=atletismo, is_proficient=True, is_expert=True, custom_bonus=1)

        self.assertEqual(character_skill.final_bonus, 8)
        self.client.force_login(self.player)
        response = self.client.post(reverse("characters:sheet", kwargs={"slug": self.c1.slug}), {"name": "Nami", "is_proficient": "", "level": 4, "max_hp": 999}, follow=True)
        self.assertEqual(response.status_code, 200)
        character.refresh_from_db()
        character_skill.refresh_from_db()
        self.assertEqual(character.level, 1)
        self.assertEqual(character.max_hp, 10)
        self.assertTrue(character_skill.is_proficient)
