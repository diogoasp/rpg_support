from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from enemies.models import ENEMY_ENVIRONMENTS

ENCOUNTER_DIFFICULTIES=[('easy','Fácil'),('medium','Médio'),('hard','Difícil')]
ENCOUNTER_STATUS=[('draft','Rascunho'),('ready','Preparado'),('started','Iniciado'),('finished','Finalizado'),('cancelled','Cancelado')]
class Encounter(models.Model):
    campaign=models.ForeignKey('campaigns.Campaign',on_delete=models.CASCADE,related_name='encounters'); name=models.CharField('nome',max_length=150); difficulty=models.CharField('dificuldade',max_length=10,choices=ENCOUNTER_DIFFICULTIES); status=models.CharField('status',max_length=12,choices=ENCOUNTER_STATUS,default='draft',db_index=True); has_boss=models.BooleanField('com chefe',default=False); environment=models.CharField('ambiente',max_length=20,choices=ENEMY_ENVIRONMENTS,blank=True); faction=models.ForeignKey('enemies.EnemyFaction',on_delete=models.SET_NULL,null=True,blank=True,related_name='encounters'); estimated_difficulty=models.CharField('estimativa de dificuldade',max_length=10,choices=ENCOUNTER_DIFFICULTIES,blank=True); estimated_threat=models.DecimalField(max_digits=10,decimal_places=2,default=0); operational_load=models.PositiveIntegerField(default=0); generator_notes=models.TextField('alertas do gerador',blank=True); master_notes=models.TextField('notas do mestre',blank=True); generation_parameters=models.JSONField(default=dict,blank=True); created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='created_encounters'); created_at=models.DateTimeField(auto_now_add=True,db_index=True); updated_at=models.DateTimeField(auto_now=True); started_at=models.DateTimeField(null=True,blank=True); finished_at=models.DateTimeField(null=True,blank=True)
    class Meta: ordering=('-created_at',); indexes=[models.Index(fields=('campaign','status'))]
    def __str__(self): return self.name
class EncounterParticipant(models.Model):
    encounter=models.ForeignKey(Encounter,on_delete=models.CASCADE,related_name='participants'); character=models.ForeignKey('characters.Character',on_delete=models.PROTECT,related_name='encounter_participations'); is_active=models.BooleanField(default=True)
    class Meta: constraints=[models.UniqueConstraint(fields=('encounter','character'),name='unique_encounter_participant')]
    def clean(self):
        errors={}
        if self.encounter_id and self.character_id and self.encounter.campaign_id!=self.character.campaign_id: errors['character']='O personagem deve pertencer à campanha.'
        if self.character_id and (not self.character.user.is_active): errors['character']='O personagem deve estar ativo.'
        if errors: raise ValidationError(errors)
class EncounterEnemy(models.Model):
    encounter=models.ForeignKey(Encounter,on_delete=models.CASCADE,related_name='enemy_groups'); enemy=models.ForeignKey('enemies.Enemy',on_delete=models.PROTECT,related_name='encounter_groups'); display_name=models.CharField(max_length=150,blank=True); quantity=models.PositiveSmallIntegerField(default=1,validators=[MinValueValidator(1)]); max_hp_override=models.PositiveIntegerField(null=True,blank=True,validators=[MinValueValidator(1)]); armor_class_override=models.PositiveSmallIntegerField(null=True,blank=True); resistance_bonus_override=models.SmallIntegerField(null=True,blank=True); is_boss=models.BooleanField(default=False); sort_order=models.PositiveSmallIntegerField(default=0); master_note=models.TextField(blank=True)
    class Meta: ordering=('sort_order','pk')
    @property
    def effective_name(self): return self.display_name or self.enemy.name
