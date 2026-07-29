from django import forms
from .models import Ship


class MultipleFileInput(forms.ClearableFileInput):
 allow_multiple_selected=True


class MultipleImageField(forms.ImageField):
 def clean(self,data,initial=None):
  single_clean=super().clean
  if isinstance(data,(list,tuple)):
   return [single_clean(item,initial) for item in data]
  return [single_clean(data,initial)] if data else []


class ShipForm(forms.ModelForm):
 additional_images=MultipleImageField(label='Imagens adicionais',required=False,widget=MultipleFileInput,help_text='Estas imagens aparecem somente na tela de detalhes da embarcação.')
 class Meta:
  model=Ship
  exclude=('campaign','belongs_to_crew','created_at','updated_at')
  labels={'image':'Imagem principal'}
  help_texts={'image':'Esta é a imagem exibida nos cards do navio e também nos detalhes.'}
class DamageShipForm(forms.Form):
 raw_damage=forms.IntegerField(label='Dano bruto',min_value=0); resistance_reduction=forms.IntegerField(label='Redução sugerida',min_value=0,required=False,initial=0); final_damage=forms.IntegerField(label='Dano final (opcional)',min_value=0,required=False)
class RepairShipForm(forms.Form): amount=forms.IntegerField(label='Quantidade reparada',min_value=1)
class NavigationResourcesForm(forms.ModelForm):
 class Meta: model=Ship; fields=('navigation_resources',)
