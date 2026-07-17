from pathlib import Path
from uuid import uuid4
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from characters.models import Character

ENEMY_CATEGORIES=[('minion','Lacaio'),('standard','Comum'),('elite','Elite'),('boss','Chefe'),('creature','Criatura'),('vehicle','Veículo'),('special','Especial')]
ENEMY_ENVIRONMENTS=[('any','Qualquer'),('urban','Urbano'),('forest','Floresta'),('desert','Deserto'),('mountain','Montanha'),('sea','Mar'),('ship','Navio'),('island','Ilha'),('underground','Subterrâneo'),('special','Especial')]
OPERATIONAL_COMPLEXITY=[('simple','Simples'),('moderate','Moderado'),('complex','Complexo')]
ENCOUNTER_MODES=[('normal','Confronto normal'),('reduced','Versão reduzida'),('narrative','Encontro narrativo'),('not_recommended','Não recomendado')]
ACTION_TYPES=[('action','Ação'),('bonus_action','Ação bônus'),('reaction','Reação'),('passive','Passiva'),('legendary','Especial'),('other','Outra')]

def enemy_image_path(instance, filename): return f"enemies/{uuid4().hex}{Path(filename).suffix.lower()}"
def validate_enemy_image(value):
    if value.size > settings.MAX_ENEMY_IMAGE_UPLOAD_SIZE: raise ValidationError('A imagem excede o limite permitido.')
    if Path(value.name).suffix.lower() not in {'.jpg','.jpeg','.png','.webp'}: raise ValidationError('Use JPEG, PNG ou WebP.')
    content_type=getattr(value,'content_type','')
    if content_type and content_type not in {'image/jpeg','image/png','image/webp'}: raise ValidationError('O tipo MIME da imagem é inválido.')

class EnemyFaction(models.Model):
    name=models.CharField('nome',max_length=120); slug=models.SlugField(unique=True); description=models.TextField('descrição',blank=True); is_active=models.BooleanField('ativa',default=True)
    class Meta: ordering=('name',)
    def __str__(self): return self.name

class Enemy(models.Model):
    name=models.CharField('nome',max_length=150); slug=models.SlugField(unique=True); image=models.ImageField('imagem',upload_to=enemy_image_path,validators=[validate_enemy_image],blank=True); description=models.TextField('descrição',blank=True)
    category=models.CharField('categoria',max_length=20,choices=ENEMY_CATEGORIES,default='standard',db_index=True); faction=models.ForeignKey(EnemyFaction,on_delete=models.SET_NULL,null=True,blank=True,related_name='enemies'); environment=models.CharField('ambiente',max_length=20,choices=ENEMY_ENVIRONMENTS,default='any',db_index=True)
    difficulty_tier=models.CharField('faixa de dificuldade',max_length=40,blank=True); challenge_rating=models.DecimalField('ND',max_digits=6,decimal_places=2,default=1); recommended_min_level=models.PositiveSmallIntegerField('nível mínimo',default=1); recommended_max_level=models.PositiveSmallIntegerField('nível máximo',default=20)
    max_hp=models.PositiveIntegerField('PV máximo',validators=[MinValueValidator(1)]); armor_class=models.PositiveSmallIntegerField('CR',default=10); resistance_bonus=models.SmallIntegerField('resistência',default=0); initiative=models.SmallIntegerField('iniciativa',default=0); movement=models.PositiveSmallIntegerField('deslocamento',default=9)
    strength=models.PositiveSmallIntegerField(default=10,validators=[MinValueValidator(1),MaxValueValidator(30)]); dexterity=models.PositiveSmallIntegerField(default=10,validators=[MinValueValidator(1),MaxValueValidator(30)]); constitution=models.PositiveSmallIntegerField(default=10,validators=[MinValueValidator(1),MaxValueValidator(30)]); intelligence=models.PositiveSmallIntegerField(default=10,validators=[MinValueValidator(1),MaxValueValidator(30)]); wisdom=models.PositiveSmallIntegerField(default=10,validators=[MinValueValidator(1),MaxValueValidator(30)]); charisma=models.PositiveSmallIntegerField(default=10,validators=[MinValueValidator(1),MaxValueValidator(30)])
    is_boss=models.BooleanField('chefe',default=False,db_index=True); is_named_character=models.BooleanField('personagem nomeado',default=False); is_canon_character=models.BooleanField('personagem canônico',default=False)
    operational_complexity=models.CharField('complexidade',max_length=20,choices=OPERATIONAL_COMPLEXITY,default='simple',db_index=True); encounter_mode=models.CharField('modo de encontro',max_length=20,choices=ENCOUNTER_MODES,default='normal',db_index=True); threat_score_override=models.DecimalField('ameaça manual',max_digits=8,decimal_places=2,null=True,blank=True)
    is_available_for_generator=models.BooleanField('disponível no gerador',default=True,db_index=True); is_active=models.BooleanField('ativo',default=True,db_index=True)
    combat_behavior=models.TextField('comportamento',blank=True); retreat_condition=models.TextField('condição de fuga',blank=True); surrender_condition=models.TextField('condição de rendição',blank=True); master_tips=models.TextField('dicas ao mestre',blank=True); notes=models.TextField('notas privadas',blank=True)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=('name',); constraints=[models.CheckConstraint(condition=models.Q(max_hp__gt=0),name='enemy_max_hp_positive'),models.CheckConstraint(condition=models.Q(recommended_max_level__gte=models.F('recommended_min_level')),name='enemy_level_range_valid')]
    def __str__(self): return self.name
    def clean(self):
        if not self.is_active: self.is_available_for_generator=False
    strength_modifier=property(lambda s:Character.modifier(s.strength)); dexterity_modifier=property(lambda s:Character.modifier(s.dexterity)); constitution_modifier=property(lambda s:Character.modifier(s.constitution)); intelligence_modifier=property(lambda s:Character.modifier(s.intelligence)); wisdom_modifier=property(lambda s:Character.modifier(s.wisdom)); charisma_modifier=property(lambda s:Character.modifier(s.charisma))

class EnemyAction(models.Model):
    enemy=models.ForeignKey(Enemy,on_delete=models.CASCADE,related_name='actions'); name=models.CharField('nome',max_length=150); description=models.TextField('descrição',blank=True); action_type=models.CharField('tipo',max_length=20,choices=ACTION_TYPES,default='action'); attack_bonus=models.SmallIntegerField(null=True,blank=True); save_dc=models.PositiveSmallIntegerField(null=True,blank=True); save_attribute=models.CharField(max_length=20,blank=True); range_text=models.CharField(max_length=100,blank=True); target_text=models.CharField(max_length=100,blank=True); damage_text=models.CharField(max_length=150,blank=True); effect_text=models.TextField(blank=True); resource_cost=models.CharField(max_length=100,blank=True); recharge_text=models.CharField(max_length=100,blank=True); is_limited=models.BooleanField(default=False); uses_per_encounter=models.PositiveSmallIntegerField(null=True,blank=True); sort_order=models.PositiveSmallIntegerField(default=0); is_active=models.BooleanField(default=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=('sort_order','name')
    def __str__(self): return self.name

class EnemyFeature(models.Model):
    enemy=models.ForeignKey(Enemy,on_delete=models.CASCADE,related_name='features'); name=models.CharField(max_length=150); description=models.TextField(blank=True); feature_type=models.CharField(max_length=50,blank=True); sort_order=models.PositiveSmallIntegerField(default=0); is_active=models.BooleanField(default=True)
    class Meta: ordering=('sort_order','name')
    def __str__(self): return self.name
