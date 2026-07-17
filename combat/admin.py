from django.contrib import admin
from .models import Combat, Combatant, CombatNote, HPChange
@admin.register(Combat)
class CombatAdmin(admin.ModelAdmin):
    list_display=("encounter","campaign","status","mode","started_at","updated_at"); list_filter=("campaign","status","mode"); search_fields=("encounter__name",); readonly_fields=("started_at","finished_at","updated_at"); list_select_related=("encounter","campaign")
@admin.register(Combatant)
class CombatantAdmin(admin.ModelAdmin):
    list_display=("display_name","combat","combatant_type","current_hp","max_hp","narrative_state","is_boss","is_active"); list_filter=("combat__campaign","combatant_type","narrative_state","is_boss","is_active"); search_fields=("display_name",); readonly_fields=("created_at","updated_at"); list_select_related=("combat","enemy","character")
admin.site.register(CombatNote)
admin.site.register(HPChange)
