from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from .validators import portrait_upload, validate_image

attribute_validators=[MinValueValidator(1),MaxValueValidator(30)]
class Character(models.Model):
    campaign=models.ForeignKey('campaigns.Campaign',on_delete=models.CASCADE,related_name='characters',db_index=True)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='characters',db_index=True)
    name=models.CharField('nome',max_length=150)
    portrait=models.ImageField('retrato',upload_to=portrait_upload,validators=[validate_image],blank=True)
    level=models.PositiveSmallIntegerField('nível',default=1,validators=[MinValueValidator(1),MaxValueValidator(settings.MAX_CHARACTER_LEVEL)])
    species=models.CharField('espécie',max_length=100,blank=True); profession=models.CharField('profissão',max_length=100,blank=True)
    combat_style=models.CharField('estilo de combate',max_length=150,blank=True); background=models.CharField('antecedente',max_length=150,blank=True)
    bounty=models.PositiveBigIntegerField('recompensa',default=0)
    armor_class=models.PositiveSmallIntegerField('CR',default=10); proficiency_bonus=models.SmallIntegerField('proficiência',default=2)
    initiative=models.SmallIntegerField('iniciativa',default=0); movement=models.PositiveSmallIntegerField('deslocamento',default=9)
    max_hp=models.PositiveIntegerField('PV máximo',default=1); current_hp=models.PositiveIntegerField('PV atual',default=1)
    max_power_points=models.PositiveIntegerField('PP máximo',default=0); current_power_points=models.PositiveIntegerField('PP atual',default=0)
    strength=models.PositiveSmallIntegerField('força',default=10,validators=attribute_validators); dexterity=models.PositiveSmallIntegerField('destreza',default=10,validators=attribute_validators)
    constitution=models.PositiveSmallIntegerField('constituição',default=10,validators=attribute_validators); intelligence=models.PositiveSmallIntegerField('inteligência',default=10,validators=attribute_validators)
    wisdom=models.PositiveSmallIntegerField('sabedoria',default=10,validators=attribute_validators); charisma=models.PositiveSmallIntegerField('carisma',default=10,validators=attribute_validators)
    haki_declared=models.BooleanField('Haki declarado',default=False); haki_trained=models.BooleanField('Haki treinado',default=False)
    devil_fruit_name=models.CharField('Akuma no Mi',max_length=150,blank=True,default=''); devil_fruit_available=models.BooleanField('Akuma no Mi disponível',default=False)
    appearance=models.TextField('aparência',blank=True); personality=models.TextField('personalidade',blank=True); dream=models.TextField('sonho',blank=True); notes=models.TextField('notas',blank=True)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=('name',); constraints=[models.UniqueConstraint(fields=('campaign','user'),name='unique_character_per_campaign_user')]
        indexes=[models.Index(fields=('campaign','user'))]
    def __str__(self): return self.name
    def clean(self):
        errors={}
        if self.current_hp>self.max_hp: errors['current_hp']='PV atual não pode exceder o máximo.'
        if self.current_power_points>self.max_power_points: errors['current_power_points']='PP atual não pode exceder o máximo.'
        if self.user_id and self.campaign_id and (not self.user.is_player or not self.campaign.players.filter(pk=self.user_id).exists()): errors['user']='O jogador deve pertencer à campanha.'
        if errors: raise ValidationError(errors)
    @staticmethod
    def modifier(value): return (value-10)//2
    strength_modifier=property(lambda s:s.modifier(s.strength)); dexterity_modifier=property(lambda s:s.modifier(s.dexterity)); constitution_modifier=property(lambda s:s.modifier(s.constitution)); intelligence_modifier=property(lambda s:s.modifier(s.intelligence)); wisdom_modifier=property(lambda s:s.modifier(s.wisdom)); charisma_modifier=property(lambda s:s.modifier(s.charisma))
    def attribute_modifier(self,key): return self.modifier(getattr(self,key))

class Skill(models.Model):
    ATTRIBUTES=[(x,x.title()) for x in ('strength','dexterity','constitution','intelligence','wisdom','charisma')]
    name=models.CharField(max_length=100); slug=models.SlugField(unique=True); related_attribute=models.CharField(max_length=20,choices=ATTRIBUTES)
    description=models.TextField(blank=True); sort_order=models.PositiveSmallIntegerField(default=0); is_active=models.BooleanField(default=True,db_index=True)
    class Meta: ordering=('sort_order','name')
    def __str__(self): return self.name
class CharacterSkill(models.Model):
    character=models.ForeignKey(Character,on_delete=models.CASCADE,related_name='skills',db_index=True); skill=models.ForeignKey(Skill,on_delete=models.PROTECT)
    is_proficient=models.BooleanField(default=False); is_expert=models.BooleanField(default=False); custom_bonus=models.SmallIntegerField(null=True,blank=True)
    class Meta: constraints=[models.UniqueConstraint(fields=('character','skill'),name='unique_character_skill')]
    def clean(self):
        if self.is_expert and not self.is_proficient: raise ValidationError({'is_expert':'Especialização exige proficiência.'})
    @property
    def final_bonus(self): return self.character.attribute_modifier(self.skill.related_attribute)+(self.character.proficiency_bonus if self.is_proficient else 0)+(self.character.proficiency_bonus if self.is_expert else 0)+(self.custom_bonus or 0)
class CharacterTechnique(models.Model):
    ACTIONS=[('action','Ação'),('bonus_action','Ação bônus'),('reaction','Reação'),('passive','Passiva'),('other','Outro')]
    character=models.ForeignKey(Character,on_delete=models.CASCADE,related_name='techniques',db_index=True); name=models.CharField(max_length=150); description=models.TextField(blank=True)
    action_type=models.CharField(max_length=20,choices=ACTIONS,default='action'); range_text=models.CharField(max_length=100,blank=True); damage_text=models.CharField(max_length=150,blank=True); cost=models.CharField(max_length=100,blank=True)
    is_available=models.BooleanField(default=True); is_featured=models.BooleanField(default=False); sort_order=models.PositiveSmallIntegerField(default=0); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=('sort_order','name')
class CharacterFeature(models.Model):
    character=models.ForeignKey(Character,on_delete=models.CASCADE,related_name='features',db_index=True); name=models.CharField(max_length=150); description=models.TextField(blank=True); source=models.CharField(max_length=100,blank=True); is_available=models.BooleanField(default=True); sort_order=models.PositiveSmallIntegerField(default=0)
    class Meta: ordering=('sort_order','name')
class CharacterCondition(models.Model):
    character=models.ForeignKey(Character,on_delete=models.CASCADE,related_name='conditions',db_index=True); name=models.CharField(max_length=100); description=models.TextField(blank=True); is_active=models.BooleanField(default=True,db_index=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=('-created_at',)
