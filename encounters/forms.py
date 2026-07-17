from django import forms
from characters.models import Character
from enemies.models import Enemy,EnemyFaction,ENEMY_ENVIRONMENTS
from .balance import get_balance
from .models import ENCOUNTER_DIFFICULTIES
class GeneratorForm(forms.Form):
 participants=forms.ModelMultipleChoiceField(label='Jogadores participantes',queryset=Character.objects.none()); difficulty=forms.ChoiceField(label='Dificuldade',choices=ENCOUNTER_DIFFICULTIES); approximate_enemy_count=forms.IntegerField(label='Quantidade aproximada',min_value=1); has_boss=forms.BooleanField(label='Com chefe',required=False); faction=forms.ModelChoiceField(label='Facção',queryset=EnemyFaction.objects.filter(is_active=True),required=False); environment=forms.ChoiceField(label='Ambiente',choices=[('', 'Qualquer')]+ENEMY_ENVIRONMENTS,required=False); required_enemy=forms.ModelChoiceField(label='Inimigo obrigatório',queryset=Enemy.objects.filter(is_active=True),required=False); notes=forms.CharField(label='Observações',widget=forms.Textarea(attrs={'rows':2}),required=False)
 def __init__(self,*a,campaign=None,**kw): super().__init__(*a,**kw); self.campaign=campaign; self.fields['participants'].queryset=Character.objects.filter(campaign=campaign,user__is_active=True).select_related('user') if campaign else Character.objects.none()
 def clean_approximate_enemy_count(self):
  value=self.cleaned_data['approximate_enemy_count']
  if value>get_balance()['max_generated_enemies']: raise forms.ValidationError('O máximo automático é 12 inimigos.')
  return value
class SaveEncounterForm(forms.Form):
 name=forms.CharField(label='Nome',max_length=150); status=forms.ChoiceField(choices=(('draft','Rascunho'),('ready','Preparado'))); master_notes=forms.CharField(required=False,widget=forms.Textarea)
