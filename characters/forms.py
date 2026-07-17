from django import forms
from .models import Character, CharacterCondition
class CharacterForm(forms.ModelForm):
    class Meta:
        model=Character; exclude=('campaign','user','created_at','updated_at')
class ResourceForm(forms.Form):
    value=forms.IntegerField(min_value=0,label='Novo valor')
class ConditionForm(forms.ModelForm):
    class Meta: model=CharacterCondition; fields=('name','description')
