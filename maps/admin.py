from django.contrib import admin
from .models import CampaignMap
@admin.register(CampaignMap)
class CampaignMapAdmin(admin.ModelAdmin):
 list_display=('title','campaign','map_type','visibility_label','visible_user_count','has_image','has_file','related_inventory_item','is_active','is_featured','created_at','updated_at')
 list_filter=('campaign','map_type','is_active','is_visible_to_players','is_featured','created_at','updated_at')
 search_fields=('title','description','campaign__name','related_inventory_item__name')
 list_select_related=('campaign','related_inventory_item')
 filter_horizontal=('visible_to_users',)
 readonly_fields=('created_at','updated_at')
 list_editable=('is_active','is_featured')
 list_per_page=30
 @admin.display(description='Jogadores visíveis')
 def visible_user_count(self,obj): return obj.visible_to_users.count()
 @admin.display(description='Imagem', boolean=True)
 def has_image(self,obj): return bool(obj.image)
 @admin.display(description='Arquivo', boolean=True)
 def has_file(self,obj): return bool(obj.file)
