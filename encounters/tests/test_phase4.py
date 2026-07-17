from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from accounts.models import User
from campaigns.models import Campaign
from characters.models import Character
from enemies.models import Enemy,EnemyFaction
from encounters.models import Encounter,EncounterEnemy,EncounterParticipant
from encounters.services import *
class Phase4Tests(TestCase):
 def setUp(self):
  self.m=User.objects.create_user('m4',role='master'); self.p=User.objects.create_user('p4',role='player'); self.c=Campaign.objects.create(name='C4',slug='c4',master=self.m); self.c.players.add(self.p); self.ch=Character.objects.create(campaign=self.c,user=self.p,name='Heroína',level=3,max_hp=30,current_hp=30,max_power_points=6,current_power_points=6,armor_class=14); self.f=EnemyFaction.objects.create(name='F',slug='f'); self.e=Enemy.objects.create(name='Comum',slug='comum',max_hp=20,faction=self.f); self.b=Enemy.objects.create(name='Chefe',slug='chefe',max_hp=60,faction=self.f,is_boss=True,category='boss',operational_complexity='complex'); self.n=Enemy.objects.create(name='Narrativo',slug='narrativo',max_hp=200,encounter_mode='narrative')
 def test_snapshot_budget_and_threat(self):
  s=build_party_snapshot([self.ch]); self.assertEqual(s.average_level,3); self.assertLess(calculate_encounter_budget(s,'easy'),calculate_encounter_budget(s,'medium')); self.assertLess(calculate_encounter_budget(s,'medium'),calculate_encounter_budget(s,'hard')); self.assertGreater(enemy_threat_score(self.b),enemy_threat_score(self.e))
 def test_generator_rules_deterministic(self):
  data=GenerateEncounterInput(self.c,[self.ch],'medium',1,False,self.f,'',None); a=generate_encounter(data,7); b=generate_encounter(data,7); self.assertEqual([x.enemy_id if hasattr(x,'enemy_id') else x.enemy.pk for x in a.selected_enemies],[x.enemy.pk for x in b.selected_enemies]); self.assertNotIn(self.n,[x.enemy for x in a.selected_enemies]); self.assertFalse(Encounter.objects.exists())
 def test_required_narrative_warns(self):
  p=generate_encounter(GenerateEncounterInput(self.c,[self.ch],'easy',1,False,None,'',self.n),1); self.assertIn(self.n,[x.enemy for x in p.selected_enemies]); self.assertTrue(any('narrativo' in x for x in p.warnings))
 def test_recalculate_and_save_duplicate(self):
  p=generate_encounter(GenerateEncounterInput(self.c,[self.ch],'easy',1),1); before=p.estimated_threat; p.selected_enemies[0].quantity=2; recalculate_encounter_proposal(p); self.assertGreater(p.estimated_threat,before); e=save_generated_encounter(actor=self.m,campaign=self.c,name='E',status='ready',difficulty='easy',proposal=p,generation_parameters={'_participant_objects':[self.ch]}); self.assertEqual(e.participants.count(),1); self.assertEqual(e.enemy_groups.count(),1); copy=duplicate_encounter(actor=self.m,encounter=e); self.assertEqual(copy.status,'draft')
 def test_relationship_validation(self):
  other=Campaign.objects.create(name='O',slug='o',master=self.m); player=User.objects.create_user('o',role='player'); other.players.add(player); ch=Character.objects.create(campaign=other,user=player,name='O'); e=Encounter.objects.create(campaign=self.c,name='E',difficulty='easy',created_by=self.m); participant=EncounterParticipant(encounter=e,character=ch)
  with self.assertRaises(ValidationError): participant.full_clean()
  group=EncounterEnemy(encounter=e,enemy=self.e,quantity=0)
  with self.assertRaises(ValidationError): group.full_clean()
 def test_permissions_and_htmx(self):
  self.client.force_login(self.p); self.assertEqual(self.client.get('/mestre/c4/encontros/').status_code,403)
  self.client.force_login(self.m); response=self.client.post('/mestre/c4/encontros/gerar/',{'participants':[self.ch.pk],'difficulty':'easy','approximate_enemy_count':1},HTTP_HX_REQUEST='true'); self.assertEqual(response.status_code,200); self.assertContains(response,'proposal')
