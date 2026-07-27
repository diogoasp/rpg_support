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
 def test_public_history_only_shows_published_records(self):
  published=SessionRecord.objects.create(campaign=self.c,session_number=2,title='Publicado',session_date=date.today(),summary='## Aberto')
  publish_session_record(user=self.m,campaign=self.c,record=published)

  response=self.client.get('/historia/')

  self.assertEqual(response.status_code,200)
  self.assertContains(response,'Publicado')
  self.assertNotContains(response,'Rascunho')
  self.assertEqual(self.client.get(f'/historia/{published.pk}/').status_code,200)
  self.assertEqual(self.client.get(f'/historia/{self.r.pk}/').status_code,404)
 def test_private_audio(self):
  self.r.audio_file=SimpleUploadedFile('a.mp3',b'a',content_type='audio/mpeg'); self.r.save(); self.client.force_login(self.p); self.assertEqual(self.client.get(f'/historia/{self.r.pk}/midia/audio/').status_code,404)
 def test_publish_htmx(self):
  self.client.force_login(self.m); response=self.client.post(f'/mestre/c/historia/{self.r.pk}/publicar/',{'confirm':'on'},HTTP_HX_REQUEST='true'); self.assertEqual(response.status_code,200); self.assertContains(response,'Publicado')
 def test_detail_renders_summary_and_transcription_as_safe_markdown(self):
  self.r.summary='## Chegada\n\n- Encontraram **pistas**.\n\n<script>alert(1)</script>'
  self.r.transcription='> Fala importante\n\n| Item | Valor |\n| --- | --- |\n| Log pose | 1 |'
  self.r.save()
  publish_session_record(user=self.m,campaign=self.c,record=self.r)
  self.client.force_login(self.p)

  response=self.client.get(f'/historia/{self.r.pk}/')

  self.assertContains(response,'<h2>Chegada</h2>',html=True)
  self.assertContains(response,'<strong>pistas</strong>',html=True)
  self.assertContains(response,'<blockquote>')
  self.assertContains(response,'<table>')
  self.assertNotContains(response,'<script>')
