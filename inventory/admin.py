from django.contrib import admin
from .models import InventoryItem
@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display=('name','character','quantity','is_visible','is_active'); list_filter=('character__campaign','is_visible','is_active'); search_fields=('name','character__name','character__user__username'); autocomplete_fields=('character',); list_select_related=('character','character__campaign','character__user'); readonly_fields=('created_at','updated_at')
    def save_model(self,request,obj,form,change): obj.full_clean(); super().save_model(request,obj,form,change)
