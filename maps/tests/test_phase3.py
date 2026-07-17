from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from campaigns.models import Campaign
from maps.models import CampaignMap
class MapTests(TestCase):
 def setUp(self):
  self.m=User.objects.create_user('m',role='master'); self.p=User.objects.create_user('p',role='player'); self.o=User.objects.create_user('o',role='player'); self.c=Campaign.objects.create(name='C',slug='c',master=self.m); self.c.players.add(self.p); self.public=CampaignMap.objects.create(campaign=self.c,title='Público',is_visible_to_players=True); self.private=CampaignMap.objects.create(campaign=self.c,title='Privado')
 def test_visibility_and_inactive(self):
  self.client.force_login(self.p); r=self.client.get('/mapas/'); self.assertContains(r,'Público'); self.assertNotContains(r,'Privado'); self.public.is_active=False; self.public.save(); self.assertNotContains(self.client.get('/mapas/'),'Público')
 def test_specific(self):
  self.public.visible_to_users.add(self.o); self.client.force_login(self.p); self.assertNotContains(self.client.get('/mapas/'),'Público')
 def test_master_toggle_fragment(self):
  self.client.force_login(self.m); r=self.client.post(f'/mestre/c/mapas/{self.private.pk}/visibilidade/',{'is_visible_to_players':'on'},HTTP_HX_REQUEST='true'); self.assertEqual(r.status_code,200); self.private.refresh_from_db(); self.assertTrue(self.private.is_visible_to_players)
 def test_private_file_denied(self):
  self.private.file=SimpleUploadedFile('x.pdf',b'%PDF',content_type='application/pdf'); self.private.save(); self.client.force_login(self.p); self.assertEqual(self.client.get(f'/mapas/{self.private.pk}/file/').status_code,404)
