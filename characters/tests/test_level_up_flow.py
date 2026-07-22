from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase

from accounts.models import User
from campaigns.models import Campaign
from characters.level_up_service import (
    authorize_level_up,
    calculate_fixed_hp_gain,
    calculate_power_points,
    complete_level_up,
    save_level_up_draft,
    start_level_up,
)
from characters.models import (
    BasicAbility,
    Character,
    CharacterBasicAbility,
    CharacterFeature,
    CharacterLevelUpAuthorization,
    CombatStyleLevel,
)


def make_character(campaign, player, **overrides):
    data = {
        "name": "Lina",
        "level": 1,
        "species": "Humano",
        "profession": "Navegador",
        "combat_style": "Atirador",
        "background": "Marinheiro",
        "proficiency_bonus": 2,
        "initiative": 1,
        "movement": 9,
        "max_hp": 10,
        "current_hp": 6,
        "max_power_points": 2,
        "current_power_points": 1,
        "hit_die_type": 8,
        "total_hit_dice": 1,
        "strength": 10,
        "dexterity": 14,
        "constitution": 14,
        "wisdom": 10,
        "willpower": 10,
        "presence": 10,
        "intelligence": 10,
        "charisma": 10,
        "favorite_weapon": "Pistola",
        "profession_grade": "Amador",
        "profession_subdivision": "Novato",
    }
    data.update(overrides)
    return Character.objects.create(campaign=campaign, user=player, **data)


class LevelUpFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_player_book_rules_1_5_7", verbosity=0)
        call_command("seed_level_progression_1_5_7", verbosity=0)

    def setUp(self):
        self.master = User.objects.create_user("master", role=User.Role.MASTER)
        self.other_master = User.objects.create_user("other-master", role=User.Role.MASTER)
        self.player = User.objects.create_user("player", role=User.Role.PLAYER)
        self.other_player = User.objects.create_user("other-player", role=User.Role.PLAYER)
        self.campaign = Campaign.objects.create(name="East Blue", slug="east-blue", master=self.master)
        self.other_campaign = Campaign.objects.create(name="Grand Line", slug="grand-line", master=self.other_master)
        self.campaign.players.add(self.player)
        self.other_campaign.players.add(self.other_player)

    def test_master_authorizes_and_duplicate_is_blocked(self):
        character = make_character(self.campaign, self.player)

        authorization = authorize_level_up(self.master, character, "Subiu após sessão.")

        self.assertEqual(authorization.status, CharacterLevelUpAuthorization.Status.PENDING)
        self.assertEqual(authorization.from_level, 1)
        self.assertEqual(authorization.to_level, 2)
        with self.assertRaises(ValidationError):
            authorize_level_up(self.master, character)

    def test_player_and_other_master_cannot_authorize(self):
        character = make_character(self.campaign, self.player)

        with self.assertRaises(PermissionDenied):
            authorize_level_up(self.player, character)
        with self.assertRaises(PermissionDenied):
            authorize_level_up(self.other_master, character)

    def test_level_2_applies_fixed_hp_pp_basic_ability_profession_and_feature(self):
        character = make_character(self.campaign, self.player)
        authorization = authorize_level_up(self.master, character)
        process = start_level_up(self.player, authorization)
        ability = BasicAbility.objects.get(slug="corpo-de-guerreiro")

        save_level_up_draft(self.player, process, selected_basic_ability=ability, keep_favorite_weapon=True)
        history = complete_level_up(self.player, process)
        character.refresh_from_db()

        self.assertEqual(character.level, 2)
        self.assertEqual(character.max_power_points, 4)
        self.assertEqual(character.current_power_points, 3)
        self.assertEqual(character.proficiency_bonus, 2)
        self.assertEqual(character.total_hit_dice, 2)
        self.assertEqual(character.max_hp, 17)
        self.assertEqual(character.current_hp, 13)
        self.assertEqual(character.profession_grade, "Amador")
        self.assertEqual(character.profession_subdivision, "Intermediário")
        self.assertTrue(CharacterBasicAbility.objects.filter(character=character, ability=ability).exists())
        self.assertTrue(CharacterFeature.objects.filter(character=character, name="Guarda Astuta").exists())
        self.assertEqual(history.fixed_hp_value, 5)

    def test_level_3_requires_and_records_style_technique(self):
        character = make_character(self.campaign, self.player, level=2, combat_style="Lutador", hit_die_type=12, max_hp=20, current_hp=10, max_power_points=4, current_power_points=1, favorite_weapon="Corporal", profession_subdivision="Intermediário")
        authorization = authorize_level_up(self.master, character)
        process = start_level_up(self.player, authorization)
        ability = BasicAbility.objects.get(slug="aprendizado-excepcional")
        style_level = CombatStyleLevel.objects.get(combat_style__name="Lutador", level=3)
        technique = style_level.technique_options.get(name="Power Shoot")

        save_level_up_draft(self.player, process, selected_basic_ability=ability, selected_technique_ids=[technique.pk], keep_favorite_weapon=True)
        history = complete_level_up(self.player, process)
        character.refresh_from_db()

        self.assertEqual(character.level, 3)
        self.assertEqual(character.max_power_points, 6)
        self.assertEqual(character.current_power_points, 3)
        self.assertEqual(character.profession_subdivision, "Veterano")
        self.assertTrue(history.techniques.filter(name="Power Shoot").exists())
        self.assertTrue(CharacterFeature.objects.filter(character=character, name="Posições de Luta").exists())

    def test_level_4_ava_plus_two_recalculates_constitution_hp_and_profession(self):
        character = make_character(self.campaign, self.player, level=3, combat_style="Ciborgue", hit_die_type=12, constitution=17, max_hp=39, current_hp=20, max_power_points=6, current_power_points=1, favorite_weapon="Bazuca", profession_subdivision="Veterano")
        authorization = authorize_level_up(self.master, character)
        process = start_level_up(self.player, authorization)

        save_level_up_draft(self.player, process, selected_attribute_increases={"mode": "plus2", "constitution": 2}, keep_favorite_weapon=True)
        history = complete_level_up(self.player, process)
        character.refresh_from_db()

        self.assertEqual(character.level, 4)
        self.assertEqual(character.constitution, 19)
        self.assertEqual(character.max_power_points, 8)
        self.assertEqual(character.current_power_points, 3)
        self.assertEqual(character.max_hp, 53)
        self.assertEqual(character.current_hp, 34)
        self.assertEqual(history.constitution_retroactive_adjustment, 4)
        self.assertEqual(character.profession_grade, "Profissional")
        self.assertEqual(character.profession_subdivision, "Novato")
        self.assertTrue(CharacterFeature.objects.filter(character=character, name="Graduação Profissional").exists())

    def test_ava_plus_one_plus_one_cannot_repeat_or_exceed_20(self):
        character = make_character(self.campaign, self.player, level=3, combat_style="Ciborgue", hit_die_type=12, constitution=20, max_hp=45, current_hp=45, max_power_points=6, current_power_points=6, favorite_weapon="Bazuca")
        authorization = authorize_level_up(self.master, character)
        process = start_level_up(self.player, authorization)

        with self.assertRaises(ValidationError):
            save_level_up_draft(self.player, process, selected_attribute_increases={"mode": "plus2", "constitution": 2}, keep_favorite_weapon=True)
        with self.assertRaises(ValidationError):
            save_level_up_draft(self.player, process, selected_attribute_increases={"mode": "plus1_plus1", "strength": 2}, keep_favorite_weapon=True)

    def test_fixed_hp_and_power_point_tables(self):
        self.assertEqual(calculate_fixed_hp_gain(8, 2), 7)
        self.assertEqual(calculate_fixed_hp_gain(10, 1), 7)
        self.assertEqual(calculate_fixed_hp_gain(12, -1), 6)
        self.assertEqual([calculate_power_points(level) for level in range(1, 5)], [2, 4, 6, 8])

    def test_existing_lunarian_guerreiro_oni_keeps_base_hp_when_leveling_to_2(self):
        character = make_character(
            self.campaign,
            self.player,
            name="Kuro",
            species="Lunariano",
            combat_style="Guerreiro-Oni",
            constitution=14,
            max_hp=30,
            current_hp=30,
            hit_die_type=12,
            favorite_weapon="Kanabo",
        )
        authorization = authorize_level_up(self.master, character)
        process = start_level_up(self.player, authorization)
        ability = BasicAbility.objects.get(slug="corpo-de-guerreiro")

        save_level_up_draft(self.player, process, selected_basic_ability=ability, keep_favorite_weapon=True)
        complete_level_up(self.player, process)
        character.refresh_from_db()

        self.assertEqual(character.level, 2)
        self.assertEqual(character.max_hp, 39)
        self.assertEqual(character.current_hp, 39)

    def test_other_player_cannot_start_authorized_process(self):
        character = make_character(self.campaign, self.player)
        authorization = authorize_level_up(self.master, character)

        with self.assertRaises(PermissionDenied):
            start_level_up(self.other_player, authorization)

    def test_completed_authorization_cannot_be_reused(self):
        character = make_character(self.campaign, self.player)
        authorization = authorize_level_up(self.master, character)
        process = start_level_up(self.player, authorization)
        ability = BasicAbility.objects.get(slug="corpo-de-guerreiro")
        save_level_up_draft(self.player, process, selected_basic_ability=ability, keep_favorite_weapon=True)
        complete_level_up(self.player, process)

        with self.assertRaises(ValidationError):
            complete_level_up(self.player, process)
