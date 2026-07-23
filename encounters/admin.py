from django.contrib import admin
from .models import Encounter,EncounterParticipant,EncounterEnemy
class ParticipantInline(admin.TabularInline): model=EncounterParticipant; extra=0; autocomplete_fields=('character',)
class EnemyInline(admin.TabularInline): model=EncounterEnemy; extra=0; autocomplete_fields=('enemy',)
@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
 list_display=('name','campaign','difficulty','estimated_difficulty','status','environment','faction','has_boss','estimated_threat','operational_load','created_by','created_at','updated_at')
 list_filter=('campaign','status','difficulty','estimated_difficulty','environment','faction','has_boss','created_at','updated_at')
 search_fields=('name','campaign__name','created_by__username','master_notes','generator_notes')
 list_select_related=('campaign','faction','created_by')
 readonly_fields=('created_at','updated_at','started_at','finished_at')
 inlines=(ParticipantInline,EnemyInline)
 list_per_page=30

@admin.register(EncounterParticipant)
class EncounterParticipantAdmin(admin.ModelAdmin):
 list_display=('encounter','campaign','character','player','is_active')
 list_filter=('encounter__campaign','is_active')
 search_fields=('encounter__name','character__name','character__user__username')
 autocomplete_fields=('encounter','character')
 list_select_related=('encounter','encounter__campaign','character','character__user')
 @admin.display(description='Campanha', ordering='encounter__campaign__name')
 def campaign(self,obj): return obj.encounter.campaign
 @admin.display(description='Jogador', ordering='character__user__username')
 def player(self,obj): return obj.character.user

@admin.register(EncounterEnemy)
class EncounterEnemyAdmin(admin.ModelAdmin):
 list_display=('effective_name','encounter','campaign','enemy','quantity','max_hp_override','armor_class_override','resistance_bonus_override','is_boss','sort_order')
 list_filter=('encounter__campaign','enemy__category','enemy__faction','is_boss')
 search_fields=('display_name','encounter__name','enemy__name','master_note')
 autocomplete_fields=('encounter','enemy')
 list_select_related=('encounter','encounter__campaign','enemy','enemy__faction')
 list_editable=('quantity','is_boss','sort_order')
 @admin.display(description='Campanha', ordering='encounter__campaign__name')
 def campaign(self,obj): return obj.encounter.campaign
