from django.contrib import admin
from .models import Ship
@admin.register(Ship)
class ShipAdmin(admin.ModelAdmin):
 list_display=('name','campaign','is_active','current_hp','max_hp','navigation_resources'); list_filter=('campaign','is_active','category','navigation_resources'); search_fields=('name','campaign__name'); list_select_related=('campaign',); readonly_fields=('created_at','updated_at')
