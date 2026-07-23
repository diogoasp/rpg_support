from django.contrib import admin
from .models import Ship
@admin.register(Ship)
class ShipAdmin(admin.ModelAdmin):
 list_display=('name','campaign','category','hp_summary','calculated_condition','resistance_class','resistance_bonus','speed','crew_summary','navigation_resources','cannons','belongs_to_crew','is_active','updated_at')
 list_filter=('campaign','category','navigation_resources','belongs_to_crew','is_active','created_at','updated_at')
 search_fields=('name','campaign__name','description','facilities','notes')
 list_select_related=('campaign',)
 readonly_fields=('created_at','updated_at')
 list_editable=('belongs_to_crew','is_active')
 list_per_page=30
 @admin.display(description='PV')
 def hp_summary(self,obj): return f'{obj.current_hp}/{obj.max_hp}'
 @admin.display(description='Tripulação')
 def crew_summary(self,obj): return f'{obj.current_crew}/{obj.max_crew}'
