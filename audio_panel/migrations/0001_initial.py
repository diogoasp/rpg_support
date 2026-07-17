# Generated manually for Phase 6.
import audio_panel.models
import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("campaigns", "0001_initial")]
    operations = [migrations.CreateModel(name="AudioAsset", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("title", models.CharField(max_length=180, verbose_name="título")), ("slug", models.SlugField(max_length=200)),
        ("audio_file", models.FileField(upload_to=audio_panel.models.audio_upload_to, verbose_name="arquivo de áudio")),
        ("category", models.CharField(choices=[("music", "Música"), ("ambience", "Ambiente"), ("npc_voice", "Fala de personagem"), ("sound_effect", "Efeito sonoro"), ("opening", "Abertura"), ("ending", "Encerramento"), ("transition", "Transição"), ("other", "Outro")], max_length=20, verbose_name="categoria")),
        ("description", models.TextField(blank=True, verbose_name="descrição")), ("character_name", models.CharField(blank=True, max_length=150, verbose_name="personagem")), ("scene_name", models.CharField(blank=True, max_length=150, verbose_name="cena")), ("tags", models.CharField(blank=True, help_text="Separe por vírgulas.", max_length=300, verbose_name="tags")),
        ("is_favorite", models.BooleanField(default=False, verbose_name="favorito")), ("is_active", models.BooleanField(default=True, verbose_name="ativo")), ("is_featured", models.BooleanField(default=False, verbose_name="destaque")),
        ("default_volume", models.DecimalField(decimal_places=3, default=1, max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)], verbose_name="volume padrão")),
        ("default_loop", models.BooleanField(default=False, verbose_name="repetir")), ("default_channel", models.CharField(choices=[("music", "Música"), ("ambience", "Ambiente"), ("effect", "Efeito ou fala")], default="effect", max_length=10, verbose_name="canal padrão")),
        ("sort_order", models.PositiveIntegerField(default=0, verbose_name="ordem")), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("last_played_at", models.DateTimeField(blank=True, null=True, verbose_name="última reprodução")), ("play_count", models.PositiveBigIntegerField(default=0, verbose_name="reproduções")),
        ("campaign", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audio_assets", to="campaigns.campaign")),
    ], options={"ordering": ("-is_favorite", "sort_order", "title"), "indexes": [models.Index(fields=["campaign", "is_active", "category"], name="audio_panel_campaig_e90e98_idx"), models.Index(fields=["campaign", "is_active", "is_favorite"], name="audio_panel_campaig_1f11ee_idx"), models.Index(fields=["campaign", "default_channel"], name="audio_panel_campaig_31262c_idx"), models.Index(fields=["campaign", "is_featured"], name="audio_panel_campaig_73d0f7_idx"), models.Index(fields=["campaign", "last_played_at"], name="audio_panel_campaig_fa8237_idx"), models.Index(fields=["campaign", "play_count"], name="audio_panel_campaig_765f4b_idx")], "constraints": [models.UniqueConstraint(fields=("campaign", "slug"), name="unique_audio_slug_per_campaign")]}),]
