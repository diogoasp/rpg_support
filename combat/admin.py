from django.contrib import admin
from .models import Combat, Combatant, CombatNote, HPChange
@admin.register(Combat)
class CombatAdmin(admin.ModelAdmin):
    list_display=("encounter","campaign","status","mode","round_number","current_turn_index","track_player_resources","result","started_at","updated_at")
    list_filter=("campaign","status","mode","track_player_resources","result","started_at","updated_at")
    search_fields=("encounter__name","campaign__name","master_notes","final_note")
    readonly_fields=("started_at","finished_at","updated_at")
    list_select_related=("encounter","campaign")
    list_per_page=30
@admin.register(Combatant)
class CombatantAdmin(admin.ModelAdmin):
    list_display=("display_name","campaign","combat","combatant_type","hp_summary","armor_class","initiative","turn_order","narrative_state","is_defeated","is_boss","is_active","updated_at")
    list_filter=("combat__campaign","combatant_type","narrative_state","is_defeated","is_boss","is_active","updated_at")
    search_fields=("display_name","enemy__name","character__name","character__user__username")
    readonly_fields=("created_at","updated_at")
    list_select_related=("combat","combat__campaign","enemy","character","character__user")
    list_editable=("turn_order","is_active")
    list_per_page=30
    @admin.display(description="Campanha", ordering="combat__campaign__name")
    def campaign(self,obj): return obj.combat.campaign
    @admin.display(description="PV")
    def hp_summary(self,obj): return f"{obj.current_hp}/{obj.max_hp}"

@admin.register(HPChange)
class HPChangeAdmin(admin.ModelAdmin):
    list_display=("combatant","campaign","previous_hp","new_hp","hp_delta","is_reverted","created_at")
    list_filter=("combatant__combat__campaign","is_reverted","created_at")
    search_fields=("combatant__display_name","combatant__combat__encounter__name")
    readonly_fields=("created_at",)
    list_select_related=("combatant","combatant__combat","combatant__combat__campaign")
    @admin.display(description="Campanha", ordering="combatant__combat__campaign__name")
    def campaign(self,obj): return obj.combatant.combat.campaign
    @admin.display(description="Diferença")
    def hp_delta(self,obj): return obj.new_hp - obj.previous_hp

@admin.register(CombatNote)
class CombatNoteAdmin(admin.ModelAdmin):
    list_display=("combat","campaign","combatant","note_type","short_text","created_at")
    list_filter=("combat__campaign","note_type","created_at")
    search_fields=("text","combat__encounter__name","combatant__display_name")
    readonly_fields=("created_at",)
    list_select_related=("combat","combat__campaign","combatant")
    @admin.display(description="Campanha", ordering="combat__campaign__name")
    def campaign(self,obj): return obj.combat.campaign
    @admin.display(description="Texto")
    def short_text(self,obj): return obj.text[:80]
