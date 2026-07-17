from django.db import models
class SessionRecord(models.Model):
 campaign=models.ForeignKey('campaigns.Campaign',on_delete=models.CASCADE,related_name='session_records'); session_number=models.PositiveIntegerField('número da sessão'); title=models.CharField('título',max_length=180); session_date=models.DateField('data da sessão')
 cover_image=models.ImageField('capa',upload_to='history/covers/',blank=True); summary=models.TextField('resumo',blank=True); audio_file=models.FileField('áudio',upload_to='history/audio/',blank=True); transcription=models.TextField('transcrição',blank=True)
 ai_summary=models.TextField(blank=True); ai_decisions=models.TextField(blank=True); ai_detected_items=models.TextField(blank=True); ai_processed_at=models.DateTimeField(null=True,blank=True)
 is_published=models.BooleanField('publicado',default=False); published_at=models.DateTimeField('publicado em',null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
 class Meta: ordering=('-session_date','-session_number'); constraints=[models.UniqueConstraint(fields=['campaign','session_number'],name='unique_session_number_per_campaign')]; indexes=[models.Index(fields=['campaign','is_published','session_date']),models.Index(fields=['campaign','session_number'])]
 def __str__(self): return f'Sessão {self.session_number}: {self.title}'
 def save(self,*args,**kwargs):
  if self.campaign_id and type(self).objects.filter(campaign_id=self.campaign_id,session_number=self.session_number).exclude(pk=self.pk).exists():
   from django.db import IntegrityError
   raise IntegrityError('unique_session_number_per_campaign')
  return super().save(*args,**kwargs)
