from django.contrib import admin
from .models import InventoryItem
@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display=('name','character','campaign','player','quantity','has_image','has_file','is_visible','is_active','created_at','updated_at')
    list_filter=('character__campaign','is_visible','is_active','created_at','updated_at')
    search_fields=('name','description','master_note','character__name','character__user__username')
    autocomplete_fields=('character',)
    list_select_related=('character','character__campaign','character__user')
    readonly_fields=('created_at','updated_at')
    list_editable=('is_visible','is_active')
    list_per_page=30
    @admin.display(description='Campanha', ordering='character__campaign__name')
    def campaign(self,obj): return obj.character.campaign
    @admin.display(description='Jogador', ordering='character__user__username')
    def player(self,obj): return obj.character.user
    @admin.display(description='Imagem', boolean=True)
    def has_image(self,obj): return bool(obj.image)
    @admin.display(description='Arquivo', boolean=True)
    def has_file(self,obj): return bool(obj.file)
    def save_model(self,request,obj,form,change): obj.full_clean(); super().save_model(request,obj,form,change)
