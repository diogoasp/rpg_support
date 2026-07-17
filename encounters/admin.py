from django.contrib import admin
from .models import Encounter,EncounterParticipant,EncounterEnemy
class ParticipantInline(admin.TabularInline): model=EncounterParticipant; extra=0; autocomplete_fields=('character',)
class EnemyInline(admin.TabularInline): model=EncounterEnemy; extra=0; autocomplete_fields=('enemy',)
@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
 list_display=('name','campaign','difficulty','estimated_difficulty','status','has_boss','created_at'); list_filter=('status','difficulty','has_boss','campaign'); search_fields=('name','campaign__name'); list_select_related=('campaign','faction','created_by'); readonly_fields=('created_at','updated_at','started_at','finished_at'); inlines=(ParticipantInline,EnemyInline); list_per_page=30
admin.site.register(EncounterParticipant); admin.site.register(EncounterEnemy)
