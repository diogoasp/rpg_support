from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from .validators import portrait_upload, validate_image

attribute_validators=[MinValueValidator(1),MaxValueValidator(30)]
CANONICAL_ATTRIBUTES=(
    ('strength','Força'),
    ('dexterity','Destreza'),
    ('constitution','Constituição'),
    ('wisdom','Sabedoria'),
    ('willpower','Vontade'),
    ('presence','Presença'),
)
RULESET_PLAYER_BOOK_1_5_7='player-book-1.5.7'
DREAM_PATH_CHOICES=(
    ('knowledge_companionship','Conhecimento pelo Companheirismo (C/C)'),
    ('freedom_companionship','Liberdade pelo Companheirismo (L/C)'),
    ('power_companionship','Poder pelo Companheirismo (P/C)'),
    ('knowledge_strength','Conhecimento pela Força (C/F)'),
    ('freedom_strength','Liberdade pela Força (L/F)'),
    ('power_strength','Poder pela Força (P/F)'),
    ('knowledge_deception','Conhecimento pela Enganação (C/E)'),
    ('freedom_deception','Liberdade pela Enganação (L/E)'),
    ('power_deception','Poder pela Enganação (P/E)'),
)

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
    willpower=models.PositiveSmallIntegerField('vontade',default=10,validators=attribute_validators); presence=models.PositiveSmallIntegerField('presença',default=10,validators=attribute_validators)
    haki_declared=models.BooleanField('Haki declarado',default=False); haki_trained=models.BooleanField('Haki treinado',default=False)
    devil_fruit_name=models.CharField('Akuma no Mi',max_length=150,blank=True,default=''); devil_fruit_available=models.BooleanField('Akuma no Mi disponível',default=False)
    age=models.CharField('idade',max_length=60,blank=True,default=''); height=models.CharField('altura',max_length=60,blank=True,default=''); weight=models.CharField('peso',max_length=60,blank=True,default=''); dream_path=models.CharField('caminho',max_length=40,choices=DREAM_PATH_CHOICES,blank=True,default='')
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
    strength_modifier=property(lambda s:s.modifier(s.strength)); dexterity_modifier=property(lambda s:s.modifier(s.dexterity)); constitution_modifier=property(lambda s:s.modifier(s.constitution)); intelligence_modifier=property(lambda s:s.modifier(s.intelligence)); wisdom_modifier=property(lambda s:s.modifier(s.wisdom)); charisma_modifier=property(lambda s:s.modifier(s.charisma)); willpower_modifier=property(lambda s:s.modifier(s.willpower)); presence_modifier=property(lambda s:s.modifier(s.presence))
    def attribute_modifier(self,key): return self.modifier(getattr(self,key))

class Skill(models.Model):
    ATTRIBUTES=list(CANONICAL_ATTRIBUTES)+[('intelligence','Inteligência legada'),('charisma','Carisma legado')]
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

class CharacterWeapon(models.Model):
    ATTRIBUTE_CHOICES=CANONICAL_ATTRIBUTES
    character=models.ForeignKey(Character,on_delete=models.CASCADE,related_name='weapons',db_index=True)
    name=models.CharField('nome',max_length=150)
    range_text=models.CharField('alcance',max_length=100,blank=True)
    damage_die=models.CharField('dado de dano',max_length=40,blank=True)
    attribute_modifier=models.CharField('modificador de atributo',max_length=20,choices=ATTRIBUTE_CHOICES,default='strength')
    weapon_type=models.CharField('tipo da arma',max_length=100)
    is_proficient=models.BooleanField('proficiente',default=False)
    is_available=models.BooleanField('disponível',default=True,db_index=True)
    sort_order=models.PositiveSmallIntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=('sort_order','name')
        indexes=[models.Index(fields=('character','is_available','weapon_type'))]
    def __str__(self): return self.name
    @property
    def attribute_modifier_value(self): return self.character.attribute_modifier(self.attribute_modifier)

class CharacterTechnique(models.Model):
    ACTIONS=[('action','Ação'),('bonus_action','Ação bônus'),('reaction','Reação'),('passive','Passiva'),('other','Outro')]
    class Category(models.TextChoices):
        ATTACK='attack','Ataque'
        SUPPORT='support','Suporte'
    class TechniqueType(models.TextChoices):
        UNARMED='unarmed','Desarmado'
        BASIC='basic','Básico'
        INNATE='innate','Técnica inata'
        COMBAT='combat','Técnica de combate'
        BUFF='buff','Buff'
        HEAL='heal','Cura'
    ATTACK_TYPES=(TechniqueType.UNARMED,TechniqueType.BASIC,TechniqueType.INNATE,TechniqueType.COMBAT)
    SUPPORT_TYPES=(TechniqueType.BUFF,TechniqueType.HEAL)
    character=models.ForeignKey(Character,on_delete=models.CASCADE,related_name='techniques',db_index=True)
    name=models.CharField(max_length=150); description=models.TextField(blank=True)
    action_type=models.CharField(max_length=20,choices=ACTIONS,default='action')
    range_text=models.CharField(max_length=100,blank=True)
    damage_text=models.CharField(max_length=150,blank=True)
    damage_die=models.CharField('dado de dano/cura',max_length=40,blank=True)
    attribute_modifier=models.CharField('modificador de atributo',max_length=20,choices=CANONICAL_ATTRIBUTES,default='strength')
    required_weapon_type=models.CharField('tipo de arma requerida',max_length=100,blank=True)
    power_points_cost=models.PositiveSmallIntegerField('PP para uso',default=0)
    category=models.CharField('categoria',max_length=20,choices=Category.choices,default=Category.ATTACK)
    technique_type=models.CharField('tipo de técnica',max_length=20,choices=TechniqueType.choices,default=TechniqueType.INNATE)
    is_available=models.BooleanField(default=True)
    is_featured=models.BooleanField(default=False)
    sort_order=models.PositiveSmallIntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)

    class Meta: 
        ordering=('sort_order','name')

    def clean(self):
        if self.category==self.Category.ATTACK and self.technique_type not in self.ATTACK_TYPES:
            raise ValidationError({'technique_type':'Ataques aceitam apenas Desarmado, Básico, Técnica inata ou Técnica de combate.'})
        if self.category==self.Category.SUPPORT and self.technique_type not in self.SUPPORT_TYPES:
            raise ValidationError({'technique_type':'Suportes aceitam apenas Buff ou Cura.'})
        if self.technique_type in (self.TechniqueType.BASIC,self.TechniqueType.COMBAT) and not self.required_weapon_type:
            raise ValidationError({'required_weapon_type':'Informe o tipo de arma requerida para este tipo de técnica.'})
    @property
    def effective_damage_die(self): return self.damage_die or self.damage_text
    @property
    def attribute_modifier_value(self): return self.character.attribute_modifier(self.attribute_modifier)
class CharacterFeature(models.Model):
    character=models.ForeignKey(Character,on_delete=models.CASCADE,related_name='features',db_index=True)
    name=models.CharField(max_length=150)
    description=models.TextField(blank=True)
    source=models.CharField(max_length=100,blank=True)
    is_available=models.BooleanField(default=True)
    sort_order=models.PositiveSmallIntegerField(default=0)
    
    class Meta: ordering=('sort_order','name')
    def __str__(self): return f"{self.character.name} - {self.name}"

class CharacterCondition(models.Model):
    character=models.ForeignKey(Character,on_delete=models.CASCADE,related_name='conditions',db_index=True); name=models.CharField(max_length=100); description=models.TextField(blank=True); is_active=models.BooleanField(default=True,db_index=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=('-created_at',)

class RuleCatalogMixin(models.Model):
    ruleset_version=models.CharField(max_length=40,default=RULESET_PLAYER_BOOK_1_5_7,db_index=True)
    slug=models.SlugField(max_length=120)
    name=models.CharField(max_length=150)
    source_pages=models.CharField(max_length=40,blank=True)
    description=models.TextField(blank=True)
    is_active=models.BooleanField(default=True,db_index=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        abstract=True
        ordering=('name',)
        constraints=[models.UniqueConstraint(fields=('ruleset_version','slug'),name='%(app_label)s_%(class)s_ruleset_slug_unique')]
    def __str__(self): return self.name

class RuleAttribute(RuleCatalogMixin):
    key=models.CharField(max_length=20)
    class Meta(RuleCatalogMixin.Meta): verbose_name='atributo de regra'; verbose_name_plural='atributos de regra'

class RuleProficiency(RuleCatalogMixin):
    class Category(models.TextChoices):
        SKILL='skill','Perícia'
        SAVING_THROW='saving_throw','Salvaguarda'
        WEAPON='weapon','Arma'
        KIT='kit','Kit'
        TOOL='tool','Ferramenta'
        FEATURE='feature','Característica'
    category=models.CharField(max_length=20,choices=Category.choices)
    related_skill=models.ForeignKey(Skill,on_delete=models.PROTECT,null=True,blank=True,related_name='rule_proficiencies')
    class Meta(RuleCatalogMixin.Meta): verbose_name='proficiência'; verbose_name_plural='proficiências'

class Species(RuleCatalogMixin):
    base_hp=models.PositiveSmallIntegerField(default=0)
    size=models.CharField(max_length=80,blank=True)
    movement=models.DecimalField(max_digits=4,decimal_places=1,default=0)
    swim_speed=models.DecimalField(max_digits=4,decimal_places=1,default=0)
    prejudice=models.CharField(max_length=120,blank=True)
    benefits=models.JSONField(default=list,blank=True)
    difficulties=models.JSONField(default=list,blank=True)
    cultural_traits=models.JSONField(default=list,blank=True)
    ancestry_rules=models.JSONField(default=dict,blank=True)
    required_choices=models.JSONField(default=list,blank=True)
    class Meta(RuleCatalogMixin.Meta): verbose_name='espécie'; verbose_name_plural='espécies'

class SpeciesVariant(RuleCatalogMixin):
    species=models.ForeignKey(Species,on_delete=models.CASCADE,related_name='variants')
    overrides=models.JSONField(default=dict,blank=True)
    effects=models.JSONField(default=list,blank=True)
    required_choices=models.JSONField(default=list,blank=True)
    class Meta(RuleCatalogMixin.Meta): verbose_name='variante'; verbose_name_plural='variantes'

class ZoanAncestryTrait(RuleCatalogMixin):
    class TraitType(models.TextChoices):
        COMMON='common','Comum'
        SPECIFIC='specific','Específico'
        PREDATOR='predator','Predador'
    trait_type=models.CharField(max_length=20,choices=TraitType.choices)
    requires_master_approval=models.BooleanField(default=True)
    carnivore_hunter_only=models.BooleanField(default=False)
    class Meta(RuleCatalogMixin.Meta): verbose_name='traço Zoan de ancestralidade'; verbose_name_plural='traços Zoan de ancestralidade'

class CombatStyle(RuleCatalogMixin):
    hit_die=models.PositiveSmallIntegerField()
    saving_throws=models.JSONField(default=list,blank=True)
    skill_choice_count=models.PositiveSmallIntegerField(default=0)
    allowed_skills=models.ManyToManyField(Skill,blank=True,related_name='combat_styles')
    any_skill_allowed=models.BooleanField(default=False)
    weapon_proficiencies=models.JSONField(default=list,blank=True)
    kit_proficiencies=models.JSONField(default=list,blank=True)
    primary_attributes=models.JSONField(default=list,blank=True)
    favorite_weapon_options=models.JSONField(default=list,blank=True)
    innate_ability_options=models.JSONField(default=list,blank=True)
    initial_equipment=models.JSONField(default=list,blank=True)
    initial_money=models.CharField(max_length=80,blank=True)
    requirements=models.JSONField(default=dict,blank=True)
    level_1_features=models.JSONField(default=list,blank=True)
    class Meta(RuleCatalogMixin.Meta): verbose_name='estilo de combate'; verbose_name_plural='estilos de combate'

class Profession(RuleCatalogMixin):
    parent=models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True,related_name='subprofessions')
    is_no_profession=models.BooleanField(default=False)
    skill_choice_count=models.PositiveSmallIntegerField(default=2)
    allowed_skills=models.ManyToManyField(Skill,blank=True,related_name='professions')
    special_trade_skill=models.CharField(max_length=120,blank=True)
    tools=models.JSONField(default=list,blank=True)
    initial_items=models.JSONField(default=list,blank=True)
    initial_work_knowledges=models.JSONField(default=list,blank=True)
    restrictions=models.JSONField(default=dict,blank=True)
    class Meta(RuleCatalogMixin.Meta): verbose_name='profissão'; verbose_name_plural='profissões'

class Background(RuleCatalogMixin):
    skill_choice_count=models.PositiveSmallIntegerField(default=2)
    allowed_skills=models.ManyToManyField(Skill,blank=True,related_name='backgrounds')
    recommended_attribute=models.CharField(max_length=20,choices=CANONICAL_ATTRIBUTES)
    special_feature_name=models.CharField(max_length=150)
    special_feature_description=models.TextField(blank=True)
    allows_master_customization=models.BooleanField(default=True)
    class Meta(RuleCatalogMixin.Meta): verbose_name='antecedente'; verbose_name_plural='antecedentes'

class CharacterAttribute(models.Model):
    character=models.ForeignKey(Character,on_delete=models.CASCADE,related_name='attribute_breakdowns')
    attribute=models.CharField(max_length=20,choices=CANONICAL_ATTRIBUTES)
    base_value=models.PositiveSmallIntegerField(default=10)
    species_bonus=models.SmallIntegerField(default=0)
    background_bonus=models.SmallIntegerField(default=0)
    other_bonus=models.SmallIntegerField(default=0)
    final_value=models.PositiveSmallIntegerField(default=10)
    class Meta:
        ordering=('attribute',)
        constraints=[models.UniqueConstraint(fields=('character','attribute'),name='unique_character_attribute_breakdown')]

class CharacterCreation(models.Model):
    class Status(models.TextChoices):
        DRAFT='draft','Rascunho'
        READY='ready','Pronto para revisão'
        COMPLETED='completed','Concluído'
        REOPENED='reopened','Reaberto'
    class AttributeMethod(models.TextChoices):
        POINT_DISTRIBUTION='point_distribution','Distribuição por pontos'
        STANDARD_ARRAY='standard_array','Conjunto padrão'
        RANDOM_4D6_DROP_LOWEST='random_4d6_drop_lowest','Aleatório 4d6'
    STEPS=('concept','species','style','profession','attributes','background','personality','pending','equipment','review')
    campaign=models.ForeignKey('campaigns.Campaign',on_delete=models.CASCADE,related_name='character_creations',db_index=True)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='character_creations',db_index=True)
    character=models.OneToOneField(Character,on_delete=models.SET_NULL,null=True,blank=True,related_name='creation_state')
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.DRAFT,db_index=True)
    current_step=models.CharField(max_length=30,default='concept')
    ruleset_version=models.CharField(max_length=40,default=RULESET_PLAYER_BOOK_1_5_7,db_index=True)
    completed_steps=models.JSONField(default=list,blank=True)
    pending_choices=models.JSONField(default=list,blank=True)
    validation_errors=models.JSONField(default=dict,blank=True)
    warnings=models.JSONField(default=list,blank=True)
    approved_by_master=models.BooleanField(default=False)
    species=models.ForeignKey(Species,on_delete=models.PROTECT,null=True,blank=True)
    species_variant=models.ForeignKey(SpeciesVariant,on_delete=models.PROTECT,null=True,blank=True)
    mixed_species_origins=models.ManyToManyField(Species,blank=True,related_name='mixed_creations')
    combat_style=models.ForeignKey(CombatStyle,on_delete=models.PROTECT,null=True,blank=True)
    profession=models.ForeignKey(Profession,on_delete=models.PROTECT,null=True,blank=True,related_name='primary_creations')
    subprofession=models.ForeignKey(Profession,on_delete=models.PROTECT,null=True,blank=True,related_name='subprofession_creations')
    background=models.ForeignKey(Background,on_delete=models.PROTECT,null=True,blank=True)
    style_skills=models.ManyToManyField(Skill,blank=True,related_name='creation_style_choices')
    profession_skills=models.ManyToManyField(Skill,blank=True,related_name='creation_profession_choices')
    background_skills=models.ManyToManyField(Skill,blank=True,related_name='creation_background_choices')
    free_skills=models.ManyToManyField(Skill,blank=True,related_name='creation_free_choices')
    name=models.CharField(max_length=150,blank=True)
    concept=models.TextField(blank=True)
    age=models.CharField(max_length=60,blank=True,default='')
    height=models.CharField(max_length=60,blank=True,default='')
    weight=models.CharField(max_length=60,blank=True,default='')
    dream_path=models.CharField(max_length=40,choices=DREAM_PATH_CHOICES,blank=True,default='')
    appearance=models.TextField(blank=True)
    personality=models.TextField(blank=True)
    dream=models.TextField(blank=True)
    ancestry_text=models.CharField(max_length=150,blank=True)
    ancestry_choices=models.JSONField(default=dict,blank=True)
    favorite_weapon=models.CharField(max_length=120,blank=True)
    innate_ability=models.CharField(max_length=150,blank=True)
    equipment_choice=models.CharField(max_length=150,blank=True)
    attribute_method=models.CharField(max_length=30,choices=AttributeMethod.choices,default=AttributeMethod.POINT_DISTRIBUTION)
    attribute_bases=models.JSONField(default=dict,blank=True)
    species_attribute_bonuses=models.JSONField(default=dict,blank=True)
    background_attribute_bonuses=models.JSONField(default=dict,blank=True)
    other_attribute_bonuses=models.JSONField(default=dict,blank=True)
    random_rolls=models.JSONField(default=list,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    completed_at=models.DateTimeField(null=True,blank=True)
    class Meta:
        ordering=('-updated_at',)
        constraints=[models.UniqueConstraint(fields=('campaign','user'),condition=models.Q(status__in=('draft','ready','reopened')),name='unique_active_character_creation_per_campaign_user')]
    def __str__(self): return self.name or f'Criação de {self.user} em {self.campaign}'

class CharacterProficiency(models.Model):
    character=models.ForeignKey(Character,on_delete=models.CASCADE,related_name='rule_proficiencies',db_index=True)
    proficiency=models.ForeignKey(RuleProficiency,on_delete=models.PROTECT)
    source_type=models.CharField(max_length=60)
    source_object_id=models.PositiveIntegerField(null=True,blank=True)
    multiplier=models.PositiveSmallIntegerField(default=1)
    is_selected=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=('character','proficiency','source_type','source_object_id'),name='unique_character_proficiency_source')]

class CharacterRuleException(models.Model):
    creation=models.ForeignKey(CharacterCreation,on_delete=models.CASCADE,related_name='rule_exceptions')
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    ignored_rule=models.CharField(max_length=150)
    justification=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=('-created_at',)
