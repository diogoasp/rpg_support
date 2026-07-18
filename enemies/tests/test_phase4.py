from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from io import StringIO
from accounts.models import User
from enemies.models import Enemy,EnemyAction,EnemyFaction,EnemyFeature
from enemies.seeds.op_enemy_manual import ENEMIES,FACTIONS
class EnemyTests(TestCase):
 def test_validation_modifiers_and_action(self):
  enemy=Enemy(name='Teste',slug='teste',max_hp=0,strength=31)
  with self.assertRaises(ValidationError): enemy.full_clean()
  enemy.max_hp=10; enemy.strength=12; enemy.full_clean(); enemy.save(); self.assertEqual(enemy.strength_modifier,1); self.assertEqual(EnemyAction.objects.create(enemy=enemy,name='Golpe').enemy,enemy)
 def test_inactive_is_unavailable(self):
  enemy=Enemy(name='X',slug='x',max_hp=1,is_active=False); enemy.full_clean(); self.assertFalse(enemy.is_available_for_generator)
 def test_player_denied_catalog(self):
  player=User.objects.create_user('p',role='player'); self.client.force_login(player); self.assertEqual(self.client.get('/mestre/inimigos/').status_code,403)
 def test_import_enemy_manual_dry_run_does_not_persist(self):
  call_command('import_enemy_manual','--dry-run',stdout=StringIO())
  self.assertFalse(Enemy.objects.filter(slug__startswith='manual-inimigos-').exists())
  self.assertFalse(EnemyFaction.objects.filter(slug__in=FACTIONS).exists())
 def test_import_enemy_manual_is_idempotent(self):
  call_command('import_enemy_manual',stdout=StringIO())
  self.assertEqual(Enemy.objects.filter(slug__startswith='manual-inimigos-').count(),len(ENEMIES))
  self.assertEqual(EnemyFaction.objects.filter(slug__in=FACTIONS).count(),len(FACTIONS))
  sample=Enemy.objects.get(slug='manual-inimigos-soldado-recruta')
  self.assertEqual(sample.name,'Soldado Recruta')
  self.assertEqual(sample.max_hp,4)
  self.assertEqual(sample.armor_class,10)
  self.assertEqual(sample.actions.count(),1)
  action_count=EnemyAction.objects.count()
  feature_count=EnemyFeature.objects.count()
  call_command('import_enemy_manual',stdout=StringIO())
  self.assertEqual(Enemy.objects.filter(slug__startswith='manual-inimigos-').count(),len(ENEMIES))
  self.assertEqual(EnemyAction.objects.count(),action_count)
  self.assertEqual(EnemyFeature.objects.count(),feature_count)
 def test_enemy_list_renders_pagination_for_imported_manual(self):
  master=User.objects.create_user('m',role='master')
  call_command('import_enemy_manual',stdout=StringIO())
  self.client.force_login(master)
  response=self.client.get(reverse('enemies:list'))
  self.assertContains(response,'74 inimigos encontrados.')
  self.assertContains(response,'Página 1 de 4')
  self.assertContains(response,'?page=2')
  self.assertEqual(len(response.context['enemies']),20)
  response=self.client.get(reverse('enemies:list'),{'category':'creature','page':2})
  self.assertContains(response,'Página 2 de')
  self.assertContains(response,'?category=creature&page=1')
