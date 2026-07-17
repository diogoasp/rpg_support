from django.contrib import admin
from .models import Enemy,EnemyFaction,EnemyAction,EnemyFeature
class ActionInline(admin.StackedInline): model=EnemyAction; extra=0
class FeatureInline(admin.StackedInline): model=EnemyFeature; extra=0
@admin.register(Enemy)
class EnemyAdmin(admin.ModelAdmin):
 list_display=('name','category','faction','max_hp','challenge_rating','operational_complexity','encounter_mode','is_boss','is_available_for_generator','is_active'); list_filter=('category','faction','environment','operational_complexity','encounter_mode','is_boss','is_active'); search_fields=('name','description'); list_select_related=('faction',); prepopulated_fields={'slug':('name',)}; readonly_fields=('created_at','updated_at'); inlines=(ActionInline,FeatureInline); list_per_page=30
@admin.register(EnemyFaction)
class FactionAdmin(admin.ModelAdmin): search_fields=('name',); prepopulated_fields={'slug':('name',)}; list_filter=('is_active',)
admin.site.register(EnemyAction); admin.site.register(EnemyFeature)
