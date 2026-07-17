from django.core.exceptions import ValidationError
from django.test import TestCase
from accounts.models import User
from enemies.models import Enemy,EnemyAction
class EnemyTests(TestCase):
 def test_validation_modifiers_and_action(self):
  enemy=Enemy(name='Teste',slug='teste',max_hp=0,strength=31)
  with self.assertRaises(ValidationError): enemy.full_clean()
  enemy.max_hp=10; enemy.strength=12; enemy.full_clean(); enemy.save(); self.assertEqual(enemy.strength_modifier,1); self.assertEqual(EnemyAction.objects.create(enemy=enemy,name='Golpe').enemy,enemy)
 def test_inactive_is_unavailable(self):
  enemy=Enemy(name='X',slug='x',max_hp=1,is_active=False); enemy.full_clean(); self.assertFalse(enemy.is_available_for_generator)
 def test_player_denied_catalog(self):
  player=User.objects.create_user('p',role='player'); self.client.force_login(player); self.assertEqual(self.client.get('/mestre/inimigos/').status_code,403)
