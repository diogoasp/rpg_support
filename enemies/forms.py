from django import forms
from .models import Enemy,EnemyAction,EnemyFeature
class EnemyForm(forms.ModelForm):
 class Meta: model=Enemy; exclude=('created_at','updated_at'); widgets={x:forms.Textarea(attrs={'rows':2}) for x in ('description','combat_behavior','retreat_condition','surrender_condition','master_tips','notes')}
EnemyActionFormSet=forms.inlineformset_factory(Enemy,EnemyAction,fields=('name','action_type','description','attack_bonus','save_dc','save_attribute','range_text','target_text','damage_text','effect_text','resource_cost','recharge_text','is_limited','uses_per_encounter','sort_order','is_active'),extra=1,can_delete=True)
EnemyFeatureFormSet=forms.inlineformset_factory(Enemy,EnemyFeature,fields=('name','feature_type','description','sort_order','is_active'),extra=1,can_delete=True)
