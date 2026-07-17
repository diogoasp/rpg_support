from django.contrib import admin

from .models import Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "master", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "master__username", "players__username")
    filter_horizontal = ("players",)
    prepopulated_fields = {"slug": ("name",)}
