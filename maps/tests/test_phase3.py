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

 def test_map_detail_displays_image_and_fullscreen_action(self):
  self.public.image=SimpleUploadedFile('mapa.png',b'png',content_type='image/png'); self.public.save()
  self.client.force_login(self.p); r=self.client.get(f'/mapas/{self.public.pk}/visualizar/')
  self.assertContains(r,'data-map-fullscreen'); self.assertContains(r,f'/mapas/{self.public.pk}/image/')
 def test_pdf_can_be_previewed_inline_and_downloaded(self):
  self.public.file=SimpleUploadedFile('mapa.pdf',b'%PDF-1.4',content_type='application/pdf'); self.public.save()
  self.client.force_login(self.p)
  preview=self.client.get(f'/mapas/{self.public.pk}/preview/'); download=self.client.get(f'/mapas/{self.public.pk}/file/')
  self.assertEqual(preview.status_code,200); self.assertIn('inline',preview['Content-Disposition'])
  self.assertEqual(download.status_code,200); self.assertIn('attachment',download['Content-Disposition'])
 def test_map_card_links_to_viewer_for_pdf(self):
  self.public.file=SimpleUploadedFile('mapa.pdf',b'%PDF-1.4',content_type='application/pdf'); self.public.save()
  self.client.force_login(self.p); r=self.client.get('/mapas/')
  self.assertContains(r,f'/mapas/{self.public.pk}/visualizar/'); self.assertContains(r,'Abrir mapa')
