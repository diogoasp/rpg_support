import uuid
from pathlib import Path

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


AUDIO_CATEGORIES = [
    ("music", "Música"), ("ambience", "Ambiente"),
    ("npc_voice", "Fala de personagem"), ("sound_effect", "Efeito sonoro"),
    ("opening", "Abertura"), ("ending", "Encerramento"),
    ("transition", "Transição"), ("other", "Outro"),
]
AUDIO_CHANNELS = [
    ("music", "Música"), ("ambience", "Ambiente"),
    ("effect", "Efeito ou fala"),
]


def audio_upload_to(instance, filename):
    """Keep user supplied names out of storage paths and isolate campaigns."""
    suffix = Path(filename).suffix.lower()
    return f"audio/campaigns/{instance.campaign_id}/{uuid.uuid4().hex}{suffix}"


class AudioAsset(models.Model):
    campaign = models.ForeignKey("campaigns.Campaign", on_delete=models.CASCADE, related_name="audio_assets")
    title = models.CharField("título", max_length=180)
    slug = models.SlugField(max_length=200)
    audio_file = models.FileField("arquivo de áudio", upload_to=audio_upload_to)
    category = models.CharField("categoria", max_length=20, choices=AUDIO_CATEGORIES)
    description = models.TextField("descrição", blank=True)
    character_name = models.CharField("personagem", max_length=150, blank=True)
    scene_name = models.CharField("cena", max_length=150, blank=True)
    tags = models.CharField("tags", max_length=300, blank=True, help_text="Separe por vírgulas.")
    is_favorite = models.BooleanField("favorito", default=False)
    is_active = models.BooleanField("ativo", default=True)
    is_featured = models.BooleanField("destaque", default=False)
    default_volume = models.DecimalField("volume padrão", max_digits=4, decimal_places=3, default=1,
        validators=[MinValueValidator(0), MaxValueValidator(1)])
    default_loop = models.BooleanField("repetir", default=False)
    default_channel = models.CharField("canal padrão", max_length=10, choices=AUDIO_CHANNELS, default="effect")
    sort_order = models.PositiveIntegerField("ordem", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_played_at = models.DateTimeField("última reprodução", null=True, blank=True)
    play_count = models.PositiveBigIntegerField("reproduções", default=0)

    class Meta:
        ordering = ("-is_favorite", "sort_order", "title")
        constraints = [models.UniqueConstraint(fields=("campaign", "slug"), name="unique_audio_slug_per_campaign")]
        indexes = [
            models.Index(fields=("campaign", "is_active", "category"), name="audio_panel_campaig_e90e98_idx"),
            models.Index(fields=("campaign", "is_active", "is_favorite"), name="audio_panel_campaig_1f11ee_idx"),
            models.Index(fields=("campaign", "default_channel"), name="audio_panel_campaig_31262c_idx"),
            models.Index(fields=("campaign", "is_featured"), name="audio_panel_campaig_73d0f7_idx"),
            models.Index(fields=("campaign", "last_played_at"), name="audio_panel_campaig_fa8237_idx"),
            models.Index(fields=("campaign", "play_count"), name="audio_panel_campaig_765f4b_idx"),
        ]

    def __str__(self):
        return self.title

    @property
    def volume_percent(self):
        return round(float(self.default_volume) * 100)
