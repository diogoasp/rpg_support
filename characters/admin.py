from django.contrib import admin
from .models import Character,Skill,CharacterSkill,CharacterTechnique,CharacterFeature,CharacterCondition
class SkillInline(admin.TabularInline): model=CharacterSkill; extra=0; autocomplete_fields=('skill',)
class TechniqueInline(admin.StackedInline): model=CharacterTechnique; extra=0
@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display=('name','campaign','user','level','current_hp','current_power_points'); list_filter=('campaign','level','haki_trained','devil_fruit_available'); search_fields=('name','user__username','campaign__name'); autocomplete_fields=('campaign','user'); list_select_related=('campaign','user'); readonly_fields=('created_at','updated_at'); inlines=(SkillInline,TechniqueInline,)
    def save_model(self,request,obj,form,change): obj.full_clean(); super().save_model(request,obj,form,change)
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin): search_fields=('name','slug'); list_filter=('related_attribute','is_active'); prepopulated_fields={'slug':('name',)}
for model in (CharacterSkill,CharacterTechnique,CharacterFeature,CharacterCondition): admin.site.register(model)
