from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("RPG", {"fields": ("role", "password_change_required")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("RPG", {"fields": ("role", "password_change_required")}),)
    list_display = (*UserAdmin.list_display, "role", "password_change_required")
    list_filter = (*UserAdmin.list_filter, "role", "password_change_required")
    actions = ("require_password_change", "clear_password_change_requirement")

    @admin.action(description="Exigir troca de senha no próximo acesso")
    def require_password_change(self, request, queryset):
        queryset.update(password_change_required=True)

    @admin.action(description="Remover exigência de troca de senha")
    def clear_password_change_requirement(self, request, queryset):
        queryset.update(password_change_required=False)
