from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from campaigns.models import Campaign
from characters.models import Character
from encounters.models import Encounter, EncounterEnemy, EncounterParticipant
from enemies.models import Enemy
from combat.models import Combatant
from combat.services import apply_damage_to_combatant, change_combatant_state, change_combat_mode, finish_combat, heal_combatant, reopen_combat, start_combat_from_encounter, undo_last_hp_change

class Phase5Tests(TestCase):
 @classmethod
 def setUpTestData(cls):
  cls.master=User.objects.create_user(username="m",password="x",role="master"); cls.player=User.objects.create_user(username="p",password="x",role="player"); cls.campaign=Campaign.objects.create(name="C",slug="c",master=cls.master); cls.campaign.players.add(cls.player)
  cls.character=Character.objects.create(campaign=cls.campaign,user=cls.player,name="Herói",max_hp=20,current_hp=18)
  cls.enemy=Enemy.objects.create(name="Guarda",slug="guarda",max_hp=40,armor_class=13,resistance_bonus=3,is_boss=True)
 def encounter(self):
  e=Encounter.objects.create(campaign=self.campaign,name="Porto",difficulty="medium",status="ready",created_by=self.master); EncounterEnemy.objects.create(encounter=e,enemy=self.enemy,quantity=2,max_hp_override=30,is_boss=True); EncounterParticipant.objects.create(encounter=e,character=self.character); return e
 def test_start_individualizes_groups_and_is_idempotent(self):
  e=self.encounter(); combat=start_combat_from_encounter(encounter=e,user=self.master); self.assertEqual(combat.combatants.filter(combatant_type="enemy").count(),2); self.assertEqual(list(combat.combatants.filter(combatant_type="enemy").values_list("display_name","current_hp")),[("Guarda 1",30),("Guarda 2",30)]); self.assertEqual(start_combat_from_encounter(encounter=e,user=self.master),combat)
 def test_hp_state_manual_override_and_undo(self):
  item=start_combat_from_encounter(encounter=self.encounter()).combatants.filter(enemy=self.enemy).first(); apply_damage_to_combatant(combatant=item,final_damage=23); self.assertEqual(item.current_hp,7); self.assertEqual(item.suggested_narrative_state,"badly_wounded"); change_combatant_state(combatant=item,state="fleeing"); heal_combatant(combatant=item,amount=99); self.assertEqual(item.current_hp,30); self.assertEqual(item.effective_narrative_state,"fleeing"); undo_last_hp_change(combatant=item); self.assertEqual(item.current_hp,7)
 def test_zero_can_remain_active(self):
  item=start_combat_from_encounter(encounter=self.encounter()).combatants.filter(enemy=self.enemy).first(); apply_damage_to_combatant(combatant=item,final_damage=99,mark_defeated_at_zero=False); self.assertEqual(item.current_hp,0); self.assertTrue(item.is_active); self.assertEqual(item.suggested_narrative_state,"defeated")
 def test_reference_exclusivity(self):
  combat=start_combat_from_encounter(encounter=self.encounter()); item=Combatant(combat=combat,enemy=self.enemy,character=self.character,combatant_type="enemy",display_name="Inválido"); self.assertRaises(ValidationError,item.full_clean)
 def test_initiative_mode_orders_and_finish_reopen_preserves(self):
  combat=start_combat_from_encounter(encounter=self.encounter()); change_combat_mode(combat=combat,mode="initiative"); orders=list(combat.combatants.order_by("turn_order").values_list("initiative",flat=True)); self.assertEqual(orders,sorted(orders,reverse=True)); count=combat.combatants.count(); finish_combat(combat=combat,result="victory"); self.assertEqual(combat.encounter.status,"finished"); reopen_combat(combat=combat); self.assertEqual(combat.combatants.count(),count)
 def test_player_forbidden_and_master_panel(self):
  combat=start_combat_from_encounter(encounter=self.encounter()); self.client.force_login(self.player); self.assertEqual(self.client.get(reverse("combat:panel",args=[combat.pk])).status_code,403); self.client.force_login(self.master); self.assertContains(self.client.get(reverse("combat:panel",args=[combat.pk])),"Guarda 1")
