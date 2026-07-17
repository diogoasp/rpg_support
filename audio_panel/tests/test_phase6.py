import tempfile
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from campaigns.models import Campaign
from audio_panel.forms import AudioAssetCreateForm
from audio_panel.models import AudioAsset
from audio_panel.services import get_recent_audio_assets, register_audio_play


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AudioPhase6Tests(TestCase):
    def setUp(self):
        self.master = User.objects.create_user(username="master-audio", password="pass", role="master")
        self.player = User.objects.create_user(username="player-audio", password="pass", role="player")
        self.other = User.objects.create_user(username="other-master", password="pass", role="master")
        self.campaign = Campaign.objects.create(name="East Blue", slug="east-blue-audio", master=self.master)
        self.campaign.players.add(self.player)
        self.asset = AudioAsset.objects.create(campaign=self.campaign, title="Mar", slug="mar", category="ambience",
            default_channel="ambience", audio_file=SimpleUploadedFile("mar.mp3", b"ID3audio", content_type="audio/mpeg"))

    def upload(self, name="theme.mp3", content_type="audio/mpeg", size=8):
        return SimpleUploadedFile(name, b"x" * size, content_type=content_type)

    def test_model_defaults_volume_and_unique_slug(self):
        self.assertTrue(self.asset.is_active)
        self.assertFalse(self.asset.is_favorite)
        self.assertEqual(self.asset.play_count, 0)
        self.asset.default_volume = 2
        with self.assertRaises(ValidationError): self.asset.full_clean()
        duplicate = AudioAsset(campaign=self.campaign, title="Outro", slug="mar", category="music", audio_file=self.upload())
        with self.assertRaises(ValidationError): duplicate.full_clean()

    def test_upload_validation(self):
        base = {"campaign": self.campaign.pk, "title": "Tema", "slug": "tema", "category": "music", "default_volume": 1, "default_channel": "music", "sort_order": 0}
        self.assertTrue(AudioAssetCreateForm(base, {"audio_file": self.upload()}, user=self.master).is_valid())
        self.assertFalse(AudioAssetCreateForm(base, {"audio_file": self.upload("bad.exe")}, user=self.master).is_valid())
        self.assertFalse(AudioAssetCreateForm(base, {"audio_file": self.upload(content_type="text/plain")}, user=self.master).is_valid())
        self.assertFalse(AudioAssetCreateForm(base, {}, user=self.master).is_valid())
        with override_settings(MAX_AUDIO_UPLOAD_SIZE=4):
            self.assertFalse(AudioAssetCreateForm(base, {"audio_file": self.upload(size=8)}, user=self.master).is_valid())

    def test_master_routes_and_protected_file(self):
        for user, status in ((self.master, 200), (self.player, 404), (self.other, 404)):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse("audio_panel:file", args=[self.asset.pk])).status_code, status)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("audio_panel:file", args=[self.asset.pk])).status_code, 302)

    def test_favorite_htmx_and_recent_registration(self):
        self.client.force_login(self.master)
        response = self.client.post(reverse("audio_panel:favorite", args=[self.asset.pk]), HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.asset.refresh_from_db(); self.assertTrue(self.asset.is_favorite)
        self.client.post(reverse("audio_panel:favorite", args=[self.asset.pk])); self.asset.refresh_from_db(); self.assertFalse(self.asset.is_favorite)
        response = self.client.post(reverse("audio_panel:register_play", args=[self.asset.pk]))
        self.assertEqual(response.status_code, 202)
        self.asset.refresh_from_db(); self.assertEqual(self.asset.play_count, 1); self.assertIsNotNone(self.asset.last_played_at)

    def test_recents_are_scoped_active_ordered_and_limited(self):
        now = timezone.now()
        assets = []
        for i in range(7):
            assets.append(AudioAsset.objects.create(campaign=self.campaign, title=f"A{i}", slug=f"a{i}", category="music", default_channel="music", audio_file=self.upload(f"a{i}.mp3"), last_played_at=now + timedelta(seconds=i)))
        self.asset.last_played_at = None; self.asset.save()
        assets[-1].is_active = False; assets[-1].save()
        recent = list(get_recent_audio_assets(user=self.master, limit=5))
        self.assertEqual(len(recent), 5); self.assertEqual(recent[0], assets[-2]); self.assertNotIn(self.asset, recent)

    def test_panel_only_for_master(self):
        self.client.force_login(self.master)
        self.assertContains(self.client.get(reverse("dashboard:master")), "Painel persistente de áudio")
        self.client.force_login(self.player)
        self.assertNotContains(self.client.get(reverse("dashboard:player")), "Painel persistente de áudio")
