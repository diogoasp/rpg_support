from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from maps.forms import validate_upload
from .models import SessionRecord
class SessionRecordForm(forms.ModelForm):
 class Meta:
  model=SessionRecord
  exclude=('campaign','is_published','published_at','created_at','updated_at','ai_summary','ai_decisions','ai_detected_items','ai_processed_at')
  widgets={
   'session_date':forms.DateInput(attrs={'type':'date'}),
   'summary':forms.Textarea(attrs={'rows':12,'placeholder':'Use Markdown: ## Título, **ênfase**, listas, links e tabelas.'}),
   'transcription':forms.Textarea(attrs={'rows':12,'placeholder':'Transcrição opcional em Markdown.'}),
  }
  help_texts={
   'summary':'Aceita Markdown para títulos, listas, links, citações e tabelas.',
   'transcription':'Aceita Markdown.',
  }
 def clean_cover_image(self):
  f=self.cleaned_data.get('cover_image');
  if f: validate_upload(f,{'image/jpeg','image/png','image/webp'},settings.MAX_IMAGE_UPLOAD_SIZE)
  return f
 def clean_audio_file(self):
  f=self.cleaned_data.get('audio_file');
  if f: validate_upload(f,{'audio/mpeg','audio/mp4','audio/x-m4a','audio/ogg','audio/wav','audio/x-wav'},settings.MAX_AUDIO_UPLOAD_SIZE)
  return f
class PublicationForm(forms.Form): confirm=forms.BooleanField(label='Confirmar publicação',required=True)
