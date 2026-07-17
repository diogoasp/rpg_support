from pathlib import Path
from uuid import uuid4
from django.conf import settings
from django.core.exceptions import ValidationError

def safe_upload_path(prefix):
    def upload(instance, filename):
        return f"{prefix}/{uuid4().hex}{Path(filename).suffix.lower()}"
    return upload

def validate_image(file):
    if file.size > settings.MAX_IMAGE_UPLOAD_SIZE: raise ValidationError("A imagem excede 5 MB.")
    if Path(file.name).suffix.lower() not in {'.jpg','.jpeg','.png','.webp'}: raise ValidationError("Use JPEG, PNG ou WebP.")

def validate_document(file):
    if file.size > settings.MAX_FILE_UPLOAD_SIZE: raise ValidationError("O arquivo excede 10 MB.")
    if Path(file.name).suffix.lower() not in {'.jpg','.jpeg','.png','.webp','.pdf'}: raise ValidationError("Formato não permitido.")
def portrait_upload(instance, filename): return safe_upload_path('characters/portraits')(instance, filename)
def inventory_image_upload(instance, filename): return safe_upload_path('inventory/images')(instance, filename)
def inventory_file_upload(instance, filename): return safe_upload_path('inventory/files')(instance, filename)
