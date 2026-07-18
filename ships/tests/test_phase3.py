from django.core.exceptions import PermissionDenied,ValidationError
from django.db import IntegrityError
from django.test import TestCase
from accounts.models import User
from campaigns.models import Campaign
from ships.models import Ship
from ships.services import assign_ship_to_crew,damage_ship,repair_ship,update_navigation_resources
class ShipTests(TestCase):
 def setUp(self):
  self.master=User.objects.create_user('m',role='master'); self.other_master=User.objects.create_user('m2',role='master'); self.player=User.objects.create_user('p',role='player'); self.outsider=User.objects.create_user('o',role='player'); self.c=Campaign.objects.create(name='C',slug='c',master=self.master); self.c.players.add(self.player); self.ship=Ship.objects.create(campaign=self.c,name='N',max_hp=100,current_hp=100,max_crew=10,current_crew=5,belongs_to_crew=True)
 def test_active_unique_and_validation(self):
  Ship.objects.create(campaign=self.c,name='X',max_hp=1,current_hp=1)
  with self.assertRaises(IntegrityError): Ship.objects.create(campaign=self.c,name='Y',max_hp=1,current_hp=1,belongs_to_crew=True)
  self.ship.current_hp=101
  with self.assertRaises(ValidationError): self.ship.full_clean()
 def test_new_ship_starts_outside_crew_and_master_assigns_it(self):
  reserve=Ship.objects.create(campaign=self.c,name='Reserva',max_hp=80,current_hp=80,max_crew=6,current_crew=0)
  self.assertFalse(reserve.belongs_to_crew)
  assigned=assign_ship_to_crew(user=self.master,campaign=self.c,ship=reserve)
  self.assertTrue(assigned.belongs_to_crew)
  self.ship.refresh_from_db()
  self.assertFalse(self.ship.belongs_to_crew)
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
 def test_player_does_not_view_pre_registered_ship_outside_crew(self):
  Ship.objects.create(campaign=self.c,name='Secreto',max_hp=80,current_hp=80,max_crew=6,current_crew=0)
  self.client.force_login(self.player)
  response=self.client.get('/navio/?campaign=c')
  self.assertContains(response,'N')
  self.assertNotContains(response,'Secreto')
 def test_master_can_view_and_manage_any_ship(self):
  reserve=Ship.objects.create(campaign=self.c,name='Reserva',max_hp=80,current_hp=80,max_crew=6,current_crew=0)
  self.client.force_login(self.other_master)
  self.assertContains(self.client.get('/navio/?campaign=c'),'N')
  self.assertContains(self.client.get('/mestre/c/navio/'),'N')
  self.assertContains(self.client.get('/mestre/c/navio/'),'Reserva')
  self.assertContains(self.client.get('/mestre/c/navio/'),'Definir como navio da tripulação')
  self.client.post(f'/mestre/c/navio/{reserve.pk}/definir-tripulacao/')
  reserve.refresh_from_db()
  self.assertTrue(reserve.belongs_to_crew)
  self.assertEqual(damage_ship(user=self.other_master,campaign=self.c,ship=self.ship,raw_damage=10).current_hp,90)
 def test_master_ship_detail_route_lists_campaign_ships_and_actions(self):
  reserve=Ship.objects.create(campaign=self.c,name='Reserva',max_hp=80,current_hp=80,max_crew=6,current_crew=0)
  self.client.force_login(self.master)
  response=self.client.get('/navio/?campaign=c')
  self.assertEqual(response.status_code,200)
  self.assertContains(response,'Navios cadastrados')
  self.assertContains(response,'N')
  self.assertContains(response,'Reserva')
  self.assertContains(response,'Editar')
  self.assertContains(response,'Excluir')
  self.assertContains(response,'Definir como navio da tripulação')
  self.client.post(f'/mestre/c/navio/{reserve.pk}/excluir/')
  reserve.refresh_from_db()
  self.assertFalse(reserve.is_active)
 def test_player_from_other_campaign_cannot_view_ship_by_slug(self):
  self.client.force_login(self.outsider)
  self.assertEqual(self.client.get('/navio/?campaign=c').status_code,403)
 def test_htmx_damage_fragment(self):
  self.client.force_login(self.master); response=self.client.post('/mestre/c/navio/dano/',{'raw_damage':10,'resistance_reduction':0},HTTP_HX_REQUEST='true'); self.assertEqual(response.status_code,200); self.assertContains(response,'ship-card')
