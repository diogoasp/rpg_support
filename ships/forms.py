from django import forms
from .models import Ship
class ShipForm(forms.ModelForm):
 class Meta: model=Ship; exclude=('campaign','created_at','updated_at')
class DamageShipForm(forms.Form):
 raw_damage=forms.IntegerField(label='Dano bruto',min_value=0); resistance_reduction=forms.IntegerField(label='Redução sugerida',min_value=0,required=False,initial=0); final_damage=forms.IntegerField(label='Dano final (opcional)',min_value=0,required=False)
class RepairShipForm(forms.Form): amount=forms.IntegerField(label='Quantidade reparada',min_value=1)
class NavigationResourcesForm(forms.ModelForm):
 class Meta: model=Ship; fields=('navigation_resources',)
