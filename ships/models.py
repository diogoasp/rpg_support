from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

SHIP_CATEGORIES=[('small','Pequeno'),('medium','Médio'),('large','Grande'),('very_large','Muito grande'),('special','Especial')]
NAVIGATION_RESOURCE_LEVELS=[('abundant','Abundantes'),('adequate','Adequados'),('low','Baixos'),('critical','Críticos'),('empty','Esgotados')]
CONDITION_THRESHOLDS=((75,'Normal'),(50,'Avariado'),(25,'Danificado'),(0,'Muito danificado'))
class Ship(models.Model):
    campaign=models.ForeignKey('campaigns.Campaign',on_delete=models.CASCADE,related_name='ships')
    name=models.CharField('nome',max_length=150); image=models.ImageField('imagem',upload_to='ships/images/',blank=True)
    category=models.CharField('categoria',max_length=20,choices=SHIP_CATEGORIES,default='medium'); description=models.TextField('descrição',blank=True)
    max_hp=models.PositiveIntegerField('PV máximo',validators=[MinValueValidator(1)]); current_hp=models.PositiveIntegerField('PV atual')
    resistance_class=models.PositiveSmallIntegerField('Classe de Resistência',default=10); resistance_bonus=models.SmallIntegerField('bônus de resistência',default=0); speed=models.CharField('velocidade',max_length=80,blank=True)
    max_crew=models.PositiveIntegerField('tripulação máxima',default=0); current_crew=models.PositiveIntegerField('tripulação atual',default=0)
    navigation_resources=models.CharField('recursos de navegação',max_length=20,choices=NAVIGATION_RESOURCE_LEVELS,default='adequate')
    cannons=models.PositiveSmallIntegerField('canhões',default=0); facilities=models.TextField('instalações',blank=True); notes=models.TextField('observações públicas',blank=True)
    belongs_to_crew=models.BooleanField('pertence à tripulação',default=False,db_index=True)
    is_active=models.BooleanField('ativo',default=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=('-belongs_to_crew','-is_active','-updated_at'); constraints=[models.UniqueConstraint(fields=['campaign'],condition=models.Q(belongs_to_crew=True,is_active=True),name='one_crew_ship_per_campaign'),models.CheckConstraint(condition=models.Q(max_hp__gt=0),name='ship_max_hp_positive'),models.CheckConstraint(condition=models.Q(current_hp__gte=0, current_hp__lte=models.F('max_hp')),name='ship_current_hp_valid'),models.CheckConstraint(condition=models.Q(max_crew__gte=0),name='ship_max_crew_nonnegative'),models.CheckConstraint(condition=models.Q(current_crew__gte=0, current_crew__lte=models.F('max_crew')),name='ship_current_crew_valid')]
        indexes=[models.Index(fields=['campaign','is_active','belongs_to_crew'])]
    def __str__(self): return self.name
    def save(self,*args,**kwargs):
        # Fail before issuing SQL so callers may safely inspect an expected
        # uniqueness error inside Django's TestCase transaction.
        if self.belongs_to_crew and self.is_active and self.campaign_id and type(self).objects.filter(campaign_id=self.campaign_id,belongs_to_crew=True,is_active=True).exclude(pk=self.pk).exists():
            from django.db import IntegrityError
            raise IntegrityError('one_crew_ship_per_campaign')
        return super().save(*args,**kwargs)
    def clean(self):
        errors={}
        if self.current_hp>self.max_hp: errors['current_hp']='O PV atual não pode superar o máximo.'
        if self.current_crew>self.max_crew: errors['current_crew']='A tripulação atual não pode superar a máxima.'
        if self.belongs_to_crew and not self.is_active: errors['belongs_to_crew']='Um navio inativo não pode pertencer à tripulação.'
        if self.belongs_to_crew and self.is_active and self.campaign_id and type(self).objects.filter(campaign_id=self.campaign_id,belongs_to_crew=True,is_active=True).exclude(pk=self.pk).exists(): errors['belongs_to_crew']='Já existe um navio definido para a tripulação nesta campanha.'
        if errors: raise ValidationError(errors)
    @property
    def hp_percentage(self): return round(self.current_hp/self.max_hp*100,1) if self.max_hp else 0.0
    @property
    def calculated_condition(self):
        if self.current_hp==0:return 'Inoperante'
        p=self.hp_percentage
        for threshold,label in CONDITION_THRESHOLDS:
            if p>threshold:return label
        return 'Muito danificado'
