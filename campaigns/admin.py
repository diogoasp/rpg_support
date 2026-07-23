from django.contrib import admin

from .models import Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "master", "player_count", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("name", "master__username", "players__username")
    filter_horizontal = ("players",)
    prepopulated_fields = {"slug": ("name",)}
    list_select_related = ("master",)
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 30

    @admin.display(description="Jogadores")
    def player_count(self, obj):
        return obj.players.count()
