from django.contrib import admin
from .models import CampaignMap
@admin.register(CampaignMap)
class CampaignMapAdmin(admin.ModelAdmin):
 list_display=('title','campaign','map_type','is_active','is_visible_to_players','is_featured'); list_filter=('campaign','map_type','is_active','is_visible_to_players','is_featured'); search_fields=('title','description'); list_select_related=('campaign',); filter_horizontal=('visible_to_users',); readonly_fields=('created_at','updated_at')
