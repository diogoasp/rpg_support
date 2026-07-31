from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_ship_image(file):
    if file.size > settings.MAX_IMAGE_UPLOAD_SIZE:
        raise ValidationError("A imagem excede 5 MB.")
    if Path(file.name).suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValidationError("Use JPEG, PNG ou WebP.")
