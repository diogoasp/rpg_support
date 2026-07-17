from pathlib import Path

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import AUDIO_CATEGORIES, AUDIO_CHANNELS, AudioAsset

ALLOWED_EXTENSIONS = {".mp3", ".ogg", ".m4a", ".wav", ".webm"}
ALLOWED_MIME_TYPES = {
    "audio/mpeg", "audio/ogg", "audio/mp4", "audio/x-m4a", "audio/wav",
    "audio/x-wav", "audio/webm", "video/webm", "application/ogg",
}


def validate_audio_upload(upload):
    if not upload:
        raise ValidationError("Selecione um arquivo de áudio.")
    if Path(upload.name).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValidationError("Formato inválido. Use MP3, OGG, M4A, WAV ou WebM.")
    if getattr(upload, "content_type", "") not in ALLOWED_MIME_TYPES:
        raise ValidationError("O tipo MIME do arquivo não é um áudio aceito.")
    if upload.size > settings.MAX_AUDIO_UPLOAD_SIZE:
        raise ValidationError("O arquivo excede o limite configurado.")
    return upload


class AudioAssetBaseForm(forms.ModelForm):
    class Meta:
        model = AudioAsset
        fields = ("campaign", "title", "slug", "audio_file", "category", "description",
                  "character_name", "scene_name", "tags", "is_favorite", "is_featured",
                  "default_volume", "default_loop", "default_channel", "sort_order")
        widgets = {"description": forms.Textarea(attrs={"rows": 3}),
                   "default_volume": forms.NumberInput(attrs={"min": 0, "max": 1, "step": .05})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["campaign"].queryset = user.mastered_campaigns.filter(is_active=True) if user else self.fields["campaign"].queryset.none()
        if self.instance.pk:
            self.fields["campaign"].disabled = True
            self.fields["audio_file"].required = False
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control")

    def clean_audio_file(self):
        upload = self.cleaned_data.get("audio_file")
        if not upload and self.instance.pk:
            return self.instance.audio_file
        return validate_audio_upload(upload)

    def clean_slug(self):
        slug = slugify(self.cleaned_data.get("slug") or self.cleaned_data.get("title", ""))
        if not slug:
            raise ValidationError("Informe um slug válido.")
        return slug

    def clean(self):
        data = super().clean()
        campaign = data.get("campaign") or getattr(self.instance, "campaign", None)
        slug = data.get("slug")
        if campaign and slug and AudioAsset.objects.filter(campaign=campaign, slug=slug).exclude(pk=self.instance.pk).exists():
            self.add_error("slug", "Já existe um áudio com este slug na campanha.")
        return data


class AudioAssetCreateForm(AudioAssetBaseForm):
    pass


class AudioAssetUpdateForm(AudioAssetBaseForm):
    pass


class AudioFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Busca")
    category = forms.ChoiceField(required=False, choices=[("", "Todas as categorias"), *AUDIO_CATEGORIES])
    character = forms.CharField(required=False, label="Personagem")
    scene = forms.CharField(required=False, label="Cena")
    favorite = forms.BooleanField(required=False, label="Somente favoritos")
    active = forms.ChoiceField(required=False, choices=(("", "Todos"), ("1", "Ativos"), ("0", "Inativos")))
    ordering = forms.ChoiceField(required=False, choices=(("title", "Título"), ("recent", "Mais recentes"), ("used", "Mais utilizados")))
