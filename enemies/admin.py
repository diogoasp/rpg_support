from django.contrib import admin
from .models import Enemy,EnemyFaction,EnemyAction,EnemyFeature
class ActionInline(admin.StackedInline): model=EnemyAction; extra=0
class FeatureInline(admin.StackedInline): model=EnemyFeature; extra=0
@admin.register(Enemy)
class EnemyAdmin(admin.ModelAdmin):
 list_display=('name','category','faction','environment','difficulty_tier','challenge_rating','level_range','max_hp','armor_class','resistance_bonus','initiative','operational_complexity','encounter_mode','is_boss','is_available_for_generator','is_active','updated_at')
 list_filter=('category','faction','environment','operational_complexity','encounter_mode','is_boss','is_named_character','is_canon_character','is_available_for_generator','is_active','created_at','updated_at')
 search_fields=('name','slug','description','combat_behavior','master_tips','notes')
 list_select_related=('faction',)
 prepopulated_fields={'slug':('name',)}
 readonly_fields=('created_at','updated_at')
 inlines=(ActionInline,FeatureInline)
 list_editable=('is_available_for_generator','is_active')
 list_per_page=30
 @admin.display(description='Níveis')
 def level_range(self,obj): return f'{obj.recommended_min_level}-{obj.recommended_max_level}'
@admin.register(EnemyFaction)
class FactionAdmin(admin.ModelAdmin):
 list_display=('name','slug','is_active')
 list_filter=('is_active',)
 search_fields=('name','slug','description')
 prepopulated_fields={'slug':('name',)}
 list_editable=('is_active',)

@admin.register(EnemyAction)
class EnemyActionAdmin(admin.ModelAdmin):
 list_display=('name','enemy','category','action_type','attack_bonus','save_dc','save_attribute','range_text','damage_text','is_limited','uses_per_encounter','is_active','sort_order')
 list_filter=('enemy__category','enemy__faction','action_type','is_limited','is_active')
 search_fields=('name','description','enemy__name','damage_text','effect_text','resource_cost','recharge_text')
 autocomplete_fields=('enemy',)
 readonly_fields=('created_at','updated_at')
 list_select_related=('enemy','enemy__faction')
 list_editable=('is_active','sort_order')
 @admin.display(description='Categoria', ordering='enemy__category')
 def category(self,obj): return obj.enemy.get_category_display()

@admin.register(EnemyFeature)
class EnemyFeatureAdmin(admin.ModelAdmin):
 list_display=('name','enemy','category','feature_type','is_active','sort_order')
 list_filter=('enemy__category','enemy__faction','feature_type','is_active')
 search_fields=('name','description','feature_type','enemy__name')
 autocomplete_fields=('enemy',)
 list_select_related=('enemy','enemy__faction')
 list_editable=('is_active','sort_order')
 @admin.display(description='Categoria', ordering='enemy__category')
 def category(self,obj): return obj.enemy.get_category_display()
