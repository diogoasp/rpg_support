from django.contrib import admin
from .models import (
    Background,
    Character,
    CharacterAttribute,
    CharacterCondition,
    CharacterCreation,
    CharacterFeature,
    CharacterProficiency,
    CharacterRuleException,
    CharacterSkill,
    CharacterTechnique,
    CombatStyle,
    Profession,
    RuleAttribute,
    RuleProficiency,
    Skill,
    Species,
    SpeciesVariant,
    ZoanAncestryTrait,
)


class SkillInline(admin.TabularInline): model=CharacterSkill; extra=0; autocomplete_fields=('skill',)
class AttributeInline(admin.TabularInline): model=CharacterAttribute; extra=0; readonly_fields=('final_value',)
class TechniqueInline(admin.StackedInline): model=CharacterTechnique; extra=0
@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display=('name','campaign','user','level','species','combat_style','profession','current_hp','current_power_points'); list_filter=('campaign','level','species','combat_style','profession','haki_trained','devil_fruit_available'); search_fields=('name','user__username','campaign__name','species','profession','combat_style'); autocomplete_fields=('campaign','user'); list_select_related=('campaign','user'); readonly_fields=('created_at','updated_at'); inlines=(AttributeInline,SkillInline,TechniqueInline,)
    def save_model(self,request,obj,form,change): obj.full_clean(); super().save_model(request,obj,form,change)
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin): search_fields=('name','slug'); list_filter=('related_attribute','is_active'); prepopulated_fields={'slug':('name',)}

@admin.register(RuleAttribute)
class RuleAttributeAdmin(admin.ModelAdmin):
    list_display=('name','key','ruleset_version','is_active'); list_filter=('ruleset_version','is_active'); search_fields=('name','key','slug'); prepopulated_fields={'slug':('name',)}

@admin.register(RuleProficiency)
class RuleProficiencyAdmin(admin.ModelAdmin):
    list_display=('name','category','related_skill','ruleset_version','is_active'); list_filter=('ruleset_version','category','is_active'); search_fields=('name','slug','related_skill__name'); autocomplete_fields=('related_skill',); prepopulated_fields={'slug':('name',)}

class SpeciesVariantInline(admin.TabularInline):
    model=SpeciesVariant; extra=0; fields=('name','slug','overrides','effects','required_choices','is_active'); prepopulated_fields={'slug':('name',)}

@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display=('name','ruleset_version','base_hp','size','movement','swim_speed','is_active'); list_filter=('ruleset_version','is_active','size'); search_fields=('name','slug','prejudice'); prepopulated_fields={'slug':('name',)}; inlines=(SpeciesVariantInline,)

@admin.register(SpeciesVariant)
class SpeciesVariantAdmin(admin.ModelAdmin):
    list_display=('name','species','ruleset_version','is_active'); list_filter=('ruleset_version','species','is_active'); search_fields=('name','slug','species__name'); autocomplete_fields=('species',); prepopulated_fields={'slug':('name',)}

@admin.register(ZoanAncestryTrait)
class ZoanAncestryTraitAdmin(admin.ModelAdmin):
    list_display=('name','trait_type','requires_master_approval','carnivore_hunter_only','ruleset_version','is_active'); list_filter=('ruleset_version','trait_type','requires_master_approval','carnivore_hunter_only','is_active'); search_fields=('name','slug'); prepopulated_fields={'slug':('name',)}

@admin.register(CombatStyle)
class CombatStyleAdmin(admin.ModelAdmin):
    list_display=('name','ruleset_version','hit_die','skill_choice_count','any_skill_allowed','is_active'); list_filter=('ruleset_version','hit_die','any_skill_allowed','is_active'); search_fields=('name','slug'); filter_horizontal=('allowed_skills',); prepopulated_fields={'slug':('name',)}

@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    list_display=('name','parent','ruleset_version','skill_choice_count','is_no_profession','is_active'); list_filter=('ruleset_version','parent','is_no_profession','is_active'); search_fields=('name','slug','parent__name'); autocomplete_fields=('parent',); filter_horizontal=('allowed_skills',); prepopulated_fields={'slug':('name',)}

@admin.register(Background)
class BackgroundAdmin(admin.ModelAdmin):
    list_display=('name','ruleset_version','recommended_attribute','skill_choice_count','is_active'); list_filter=('ruleset_version','recommended_attribute','is_active'); search_fields=('name','slug','special_feature_name'); filter_horizontal=('allowed_skills',); prepopulated_fields={'slug':('name',)}

@admin.register(CharacterCreation)
class CharacterCreationAdmin(admin.ModelAdmin):
    list_display=('name','campaign','user','status','current_step','species','species_variant','combat_style','profession','background','updated_at'); list_filter=('status','current_step','ruleset_version','species','combat_style','profession','background','approved_by_master'); search_fields=('name','user__username','campaign__name'); autocomplete_fields=('campaign','user','character','species','species_variant','combat_style','profession','subprofession','background'); filter_horizontal=('mixed_species_origins','style_skills','profession_skills','background_skills','free_skills'); readonly_fields=('created_at','updated_at','completed_at')

@admin.register(CharacterAttribute)
class CharacterAttributeAdmin(admin.ModelAdmin):
    list_display=('character','attribute','base_value','species_bonus','background_bonus','other_bonus','final_value'); list_filter=('attribute',); search_fields=('character__name',); autocomplete_fields=('character',)

@admin.register(CharacterProficiency)
class CharacterProficiencyAdmin(admin.ModelAdmin):
    list_display=('character','proficiency','source_type','multiplier','is_selected','created_at'); list_filter=('source_type','multiplier','is_selected'); search_fields=('character__name','proficiency__name'); autocomplete_fields=('character','proficiency'); readonly_fields=('created_at',)

@admin.register(CharacterRuleException)
class CharacterRuleExceptionAdmin(admin.ModelAdmin):
    list_display=('creation','user','ignored_rule','created_at'); list_filter=('ignored_rule','created_at'); search_fields=('creation__name','user__username','ignored_rule','justification'); autocomplete_fields=('creation','user'); readonly_fields=('created_at',)

for model in (CharacterSkill,CharacterTechnique,CharacterFeature,CharacterCondition): admin.site.register(model)
