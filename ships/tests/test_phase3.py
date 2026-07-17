from django.core.exceptions import PermissionDenied,ValidationError
from django.db import IntegrityError
from django.test import TestCase
from accounts.models import User
from campaigns.models import Campaign
from ships.models import Ship
from ships.services import damage_ship,repair_ship,update_navigation_resources
class ShipTests(TestCase):
 def setUp(self):
  self.master=User.objects.create_user('m',role='master'); self.player=User.objects.create_user('p',role='player'); self.c=Campaign.objects.create(name='C',slug='c',master=self.master); self.c.players.add(self.player); self.ship=Ship.objects.create(campaign=self.c,name='N',max_hp=100,current_hp=100,max_crew=10,current_crew=5)
 def test_active_unique_and_validation(self):
  with self.assertRaises(IntegrityError): Ship.objects.create(campaign=self.c,name='X',max_hp=1,current_hp=1)
  self.ship.current_hp=101
  with self.assertRaises(ValidationError): self.ship.full_clean()
 def test_conditions_all_ranges(self):
  for hp,label in [(100,'Normal'),(75,'Avariado'),(50,'Danificado'),(25,'Muito danificado'),(0,'Inoperante')]: self.ship.current_hp=hp; self.assertEqual(self.ship.calculated_condition,label)
  self.assertEqual(self.ship.hp_percentage,0)
 def test_services_clamp(self):
  self.ship=damage_ship(user=self.master,campaign=self.c,ship=self.ship,raw_damage=200); self.assertEqual(self.ship.current_hp,0)
  self.ship=repair_ship(user=self.master,campaign=self.c,ship=self.ship,amount=200); self.assertEqual(self.ship.current_hp,100)
  self.assertEqual(update_navigation_resources(user=self.master,campaign=self.c,ship=self.ship,level='critical').navigation_resources,'critical')
 def test_player_cannot_damage_and_can_view(self):
  with self.assertRaises(PermissionDenied): damage_ship(user=self.player,campaign=self.c,ship=self.ship,raw_damage=1)
  self.client.force_login(self.player); self.assertContains(self.client.get('/navio/?campaign=c'),'N')
 def test_htmx_damage_fragment(self):
  self.client.force_login(self.master); response=self.client.post('/mestre/c/navio/dano/',{'raw_damage':10,'resistance_reduction':0},HTTP_HX_REQUEST='true'); self.assertEqual(response.status_code,200); self.assertContains(response,'ship-card')
