from django.contrib import admin
from .models import (
    Background,
    Character,
    CharacterAttribute,
    CharacterCondition,
    CharacterCreation,
    CharacterFeature,
    CharacterHitPointComponent,
    CharacterLevelUp,
    CharacterLevelUpAuthorization,
    CharacterLevelUpCorrection,
    CharacterLevelUpHistory,
    CharacterProficiency,
    CharacterRuleException,
    CharacterSkill,
    CharacterTechnique,
    CharacterWeapon,
    CombatStyle,
    CombatStyleLevel,
    CombatStyleLevelFeature,
    CombatStyleTechniqueOption,
    BasicAbility,
    CharacterBasicAbility,
    LevelChoiceGroup,
    Profession,
    ProfessionProgression,
    RuleAttribute,
    RuleProficiency,
    Skill,
    Species,
    SpeciesVariant,
    ZoanAncestryTrait,
)


class SkillInline(admin.TabularInline): model=CharacterSkill; extra=0; autocomplete_fields=('skill',)
class AttributeInline(admin.TabularInline): model=CharacterAttribute; extra=0; readonly_fields=('final_value',)
class WeaponInline(admin.StackedInline): model=CharacterWeapon; extra=0
class TechniqueInline(admin.StackedInline): model=CharacterTechnique; extra=0
class HitPointComponentInline(admin.TabularInline): model=CharacterHitPointComponent; extra=0; readonly_fields=('created_at',)
@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display=('name','campaign','user','level','species','combat_style','profession','current_hp','current_power_points'); list_filter=('campaign','level','species','combat_style','profession','haki_trained','devil_fruit_available'); search_fields=('name','user__username','campaign__name','species','profession','combat_style'); autocomplete_fields=('campaign','user'); list_select_related=('campaign','user'); readonly_fields=('created_at','updated_at'); inlines=(AttributeInline,SkillInline,WeaponInline,TechniqueInline,HitPointComponentInline,)
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

class CombatStyleLevelFeatureInline(admin.TabularInline): model=CombatStyleLevelFeature; extra=0
class CombatStyleTechniqueOptionInline(admin.TabularInline): model=CombatStyleTechniqueOption; extra=0
class LevelChoiceGroupInline(admin.TabularInline): model=LevelChoiceGroup; extra=0
@admin.register(CombatStyleLevel)
class CombatStyleLevelAdmin(admin.ModelAdmin):
    list_display=('combat_style','level','proficiency_bonus','power_points','grants_basic_ability','grants_attribute_increase','grants_techniques','ruleset_version')
    list_filter=('ruleset_version','level','grants_basic_ability','grants_attribute_increase','grants_techniques')
    autocomplete_fields=('combat_style',)
    inlines=(CombatStyleLevelFeatureInline,CombatStyleTechniqueOptionInline,LevelChoiceGroupInline)

@admin.register(BasicAbility)
class BasicAbilityAdmin(admin.ModelAdmin):
    list_display=('name','category','repeatable','ruleset_version','is_active')
    list_filter=('category','repeatable','ruleset_version','is_active')
    search_fields=('name','slug')
    prepopulated_fields={'slug':('name',)}

@admin.register(ProfessionProgression)
class ProfessionProgressionAdmin(admin.ModelAdmin):
    list_display=('level','grade','subdivision','grants_professional_feature','ruleset_version')
    list_filter=('ruleset_version','level','grade')

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

@admin.register(CharacterWeapon)
class CharacterWeaponAdmin(admin.ModelAdmin):
    list_display=('name','character','weapon_type','range_text','damage_die','attribute_modifier','is_proficient','is_available')
    list_filter=('weapon_type','attribute_modifier','is_proficient','is_available')
    search_fields=('name','character__name','weapon_type')
    autocomplete_fields=('character',)

@admin.register(CharacterTechnique)
class CharacterTechniqueAdmin(admin.ModelAdmin):
    list_display=('name','character','category','technique_type','required_weapon_type','range_text','damage_die','power_points_cost','is_available')
    list_filter=('category','technique_type','required_weapon_type','attribute_modifier','is_available')
    search_fields=('name','character__name','required_weapon_type','description')
    autocomplete_fields=('character',)
    def save_model(self,request,obj,form,change): obj.full_clean(); super().save_model(request,obj,form,change)

@admin.register(CharacterLevelUpAuthorization)
class CharacterLevelUpAuthorizationAdmin(admin.ModelAdmin):
    list_display=('character','campaign','from_level','to_level','status','authorized_by','created_at','completed_at','cancelled_at')
    list_filter=('status','ruleset_version','from_level','to_level')
    search_fields=('character__name','campaign__name','authorized_by__username')
    autocomplete_fields=('character','campaign','authorized_by')
    readonly_fields=('created_at','started_at','completed_at','cancelled_at')

@admin.register(CharacterLevelUp)
class CharacterLevelUpAdmin(admin.ModelAdmin):
    list_display=('character','from_level','to_level','status','fixed_hp_value','old_max_hp','new_max_hp','created_at','completed_at')
    list_filter=('status','from_level','to_level')
    search_fields=('character__name','authorization__character__name')
    autocomplete_fields=('authorization','character','combat_style','selected_basic_ability')
    filter_horizontal=('selected_techniques',)
    readonly_fields=('created_at','completed_at')

@admin.register(CharacterLevelUpHistory)
class CharacterLevelUpHistoryAdmin(admin.ModelAdmin):
    list_display=('character','from_level','to_level','authorized_by','completed_by','created_at')
    list_filter=('from_level','to_level','created_at')
    autocomplete_fields=('authorization','level_up','character','authorized_by','completed_by','basic_ability')
    filter_horizontal=('techniques',)
    readonly_fields=('created_at',)

for model in (CharacterSkill,CharacterFeature,CharacterCondition,CharacterBasicAbility,CharacterLevelUpCorrection): admin.site.register(model)
