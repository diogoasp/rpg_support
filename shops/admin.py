from django.contrib import admin

from .models import Shop, ShopAccess, ShopItem


class ShopItemInline(admin.TabularInline):
    model = ShopItem
    extra = 1


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "campaign")
    list_filter = ("campaign", "city")
    search_fields = ("name", "description", "city")
    inlines = (ShopItemInline,)


@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = ("name", "shop", "price", "quantity")
    list_filter = ("shop__campaign", "shop")
    search_fields = ("name", "description", "shop__name")
    autocomplete_fields = ("shop",)


@admin.register(ShopAccess)
class ShopAccessAdmin(admin.ModelAdmin):
    list_display = ("shop", "character")
    list_filter = ("shop__campaign", "shop")
