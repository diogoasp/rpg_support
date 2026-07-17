from datetime import date
from django.test import TestCase
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from campaigns.models import Campaign
from history.models import SessionRecord
from history.services import publish_session_record,unpublish_session_record
class HistoryTests(TestCase):
 def setUp(self):
  self.m=User.objects.create_user('m',role='master'); self.p=User.objects.create_user('p',role='player'); self.c=Campaign.objects.create(name='C',slug='c',master=self.m); self.c.players.add(self.p); self.r=SessionRecord.objects.create(campaign=self.c,session_number=1,title='Rascunho',session_date=date.today())
 def test_unique_and_visibility(self):
  with self.assertRaises(IntegrityError): SessionRecord.objects.create(campaign=self.c,session_number=1,title='X',session_date=date.today())
  self.client.force_login(self.p); self.assertNotContains(self.client.get('/historia/'),'Rascunho'); publish_session_record(user=self.m,campaign=self.c,record=self.r); self.assertIsNotNone(self.r.published_at); self.assertContains(self.client.get('/historia/'),'Rascunho'); unpublish_session_record(user=self.m,campaign=self.c,record=self.r); self.assertNotContains(self.client.get('/historia/'),'Rascunho')
 def test_private_audio(self):
  self.r.audio_file=SimpleUploadedFile('a.mp3',b'a',content_type='audio/mpeg'); self.r.save(); self.client.force_login(self.p); self.assertEqual(self.client.get(f'/historia/{self.r.pk}/midia/audio/').status_code,404)
 def test_publish_htmx(self):
  self.client.force_login(self.m); response=self.client.post(f'/mestre/c/historia/{self.r.pk}/publicar/',{'confirm':'on'},HTTP_HX_REQUEST='true'); self.assertEqual(response.status_code,200); self.assertContains(response,'Publicado')
