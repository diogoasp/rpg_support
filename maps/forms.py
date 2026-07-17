import mimetypes
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import CampaignMap
def validate_upload(f,allowed,max_size):
 if f.size>max_size: raise ValidationError('Arquivo excede o limite configurado.')
 mime=getattr(f,'content_type',None) or mimetypes.guess_type(f.name)[0]
 if mime not in allowed: raise ValidationError('Tipo de arquivo não permitido.')
class CampaignMapForm(forms.ModelForm):
 class Meta: model=CampaignMap; exclude=('campaign','created_at','updated_at')
 def clean_image(self):
  f=self.cleaned_data.get('image');
  if f: validate_upload(f,{'image/jpeg','image/png','image/webp'},settings.MAX_IMAGE_UPLOAD_SIZE)
  return f
 def clean_file(self):
  f=self.cleaned_data.get('file');
  if f: validate_upload(f,{'application/pdf'},settings.MAX_DOCUMENT_UPLOAD_SIZE)
  return f
class MapVisibilityForm(forms.ModelForm):
 class Meta: model=CampaignMap; fields=('is_visible_to_players','visible_to_users')
