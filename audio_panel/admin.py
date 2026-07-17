from django.contrib import admin
from .models import AudioAsset


@admin.register(AudioAsset)
class AudioAssetAdmin(admin.ModelAdmin):
    list_display = ("title", "campaign", "category", "default_channel", "is_favorite", "is_active", "play_count")
    list_filter = ("campaign", "category", "default_channel", "is_favorite", "is_active", "character_name", "scene_name")
    search_fields = ("title", "character_name", "scene_name", "tags")
    ordering = ("campaign", "sort_order", "title")
    readonly_fields = ("created_at", "updated_at", "last_played_at", "play_count")
    list_select_related = ("campaign",)
