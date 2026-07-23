from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from campaigns.models import Campaign
from characters.models import Character
from combat.models import Combatant
from combat.services import (
    apply_damage_to_combatant,
    change_combat_mode,
    change_combatant_state,
    finish_combat,
    heal_combatant,
    reopen_combat,
    start_combat_from_encounter,
    undo_last_hp_change,
)
from encounters.models import Encounter, EncounterEnemy, EncounterParticipant
from enemies.models import Enemy


class Phase5Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.master = User.objects.create_user(username="m", password="x", role="master")
        cls.player = User.objects.create_user(username="p", password="x", role="player")
        cls.campaign = Campaign.objects.create(name="C", slug="c", master=cls.master)
        cls.campaign.players.add(cls.player)
        cls.character = Character.objects.create(campaign=cls.campaign, user=cls.player, name="Herói", max_hp=20, current_hp=18)
        cls.enemy = Enemy.objects.create(name="Guarda", slug="guarda", max_hp=40, armor_class=13, resistance_bonus=3, is_boss=True)

    def encounter(self):
        encounter = Encounter.objects.create(campaign=self.campaign, name="Porto", difficulty="medium", status="ready", created_by=self.master)
        EncounterEnemy.objects.create(encounter=encounter, enemy=self.enemy, quantity=2, max_hp_override=30, is_boss=True)
        EncounterParticipant.objects.create(encounter=encounter, character=self.character)
        return encounter

    def test_start_individualizes_groups_and_is_idempotent(self):
        encounter = self.encounter()
        combat = start_combat_from_encounter(encounter=encounter, user=self.master)
        self.assertEqual(combat.combatants.filter(combatant_type="enemy").count(), 2)
        self.assertEqual(
            list(combat.combatants.filter(combatant_type="enemy").values_list("display_name", "current_hp")),
            [("Guarda 1", 30), ("Guarda 2", 30)],
        )
        self.assertEqual(start_combat_from_encounter(encounter=encounter, user=self.master), combat)

    def test_hp_state_manual_override_and_undo(self):
        item = start_combat_from_encounter(encounter=self.encounter()).combatants.filter(enemy=self.enemy).first()
        apply_damage_to_combatant(combatant=item, final_damage=23)
        self.assertEqual(item.current_hp, 7)
        self.assertEqual(item.suggested_narrative_state, "badly_wounded")
        change_combatant_state(combatant=item, state="fleeing")
        heal_combatant(combatant=item, amount=99)
        self.assertEqual(item.current_hp, 30)
        self.assertEqual(item.effective_narrative_state, "fleeing")
        undo_last_hp_change(combatant=item)
        self.assertEqual(item.current_hp, 7)

    def test_zero_can_remain_active(self):
        item = start_combat_from_encounter(encounter=self.encounter()).combatants.filter(enemy=self.enemy).first()
        apply_damage_to_combatant(combatant=item, final_damage=99, mark_defeated_at_zero=False)
        self.assertEqual(item.current_hp, 0)
        self.assertTrue(item.is_active)
        self.assertEqual(item.suggested_narrative_state, "defeated")

    def test_player_combatant_hp_updates_character_and_player_dashboard(self):
        combat = start_combat_from_encounter(encounter=self.encounter())
        item = combat.combatants.get(character=self.character)

        apply_damage_to_combatant(combatant=item, final_damage=5)
        self.character.refresh_from_db()
        self.assertEqual(self.character.current_hp, 13)

        self.client.force_login(self.player)
        response = self.client.get(reverse("characters:dashboard", kwargs={"slug": self.campaign.slug}))
        self.assertContains(response, "13/20")

        heal_combatant(combatant=item, amount=4)
        self.character.refresh_from_db()
        self.assertEqual(self.character.current_hp, 17)

        undo_last_hp_change(combatant=item)
        self.character.refresh_from_db()
        self.assertEqual(self.character.current_hp, 13)

    def test_master_damage_and_heal_combatant_actions_update_card_and_close_modal(self):
        combat = start_combat_from_encounter(encounter=self.encounter())
        item = combat.combatants.filter(enemy=self.enemy).first()
        self.client.force_login(self.master)

        response = self.client.post(
            reverse("combat:damage", args=[combat.pk, item.pk]),
            {"raw_damage": 6, "reduction": "", "final_damage": "", "mark_defeated_at_zero": "on"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["HX-Trigger"], "modal:close")
        self.assertContains(response, "24/30")
        item.refresh_from_db()
        self.assertEqual(item.current_hp, 24)

        response = self.client.post(reverse("combat:heal", args=[combat.pk, item.pk]), {"amount": 4}, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["HX-Trigger"], "modal:close")
        self.assertContains(response, "28/30")
        item.refresh_from_db()
        self.assertEqual(item.current_hp, 28)

    def test_combatant_damage_validation_stays_in_modal(self):
        combat = start_combat_from_encounter(encounter=self.encounter())
        item = combat.combatants.filter(enemy=self.enemy).first()
        self.client.force_login(self.master)

        response = self.client.post(reverse("combat:damage", args=[combat.pk, item.pk]), {}, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.headers["HX-Retarget"], "#modal-content")
        self.assertEqual(response.headers["HX-Reswap"], "innerHTML")

    def test_reference_exclusivity(self):
        combat = start_combat_from_encounter(encounter=self.encounter())
        item = Combatant(combat=combat, enemy=self.enemy, character=self.character, combatant_type="enemy", display_name="Inválido")
        self.assertRaises(ValidationError, item.full_clean)

    def test_initiative_mode_orders_and_finish_reopen_preserves(self):
        combat = start_combat_from_encounter(encounter=self.encounter())
        change_combat_mode(combat=combat, mode="initiative")
        orders = list(combat.combatants.order_by("turn_order").values_list("initiative", flat=True))
        self.assertEqual(orders, sorted(orders, reverse=True))
        count = combat.combatants.count()
        finish_combat(combat=combat, result="victory")
        self.assertEqual(combat.encounter.status, "finished")
        reopen_combat(combat=combat)
        self.assertEqual(combat.combatants.count(), count)

    def test_player_forbidden_and_master_panel(self):
        combat = start_combat_from_encounter(encounter=self.encounter())
        self.client.force_login(self.player)
        self.assertEqual(self.client.get(reverse("combat:panel", args=[combat.pk])).status_code, 403)
        self.client.force_login(self.master)
        self.assertContains(self.client.get(reverse("combat:panel", args=[combat.pk])), "Guarda 1")
