from .creation_catalog_service import allowed_background_skills, allowed_profession_skills, allowed_style_skills, allowed_subprofessions, variants_for_species


def dependent_fields_for_change(field):
    return {
        "species": ["species_variant", "mixed_species_origins", "ancestry_text", "ancestry_choices", "species_attribute_bonuses"],
        "species_variant": ["ancestry_choices"],
        "combat_style": ["style_skills", "favorite_weapon", "innate_ability", "equipment_choice"],
        "profession": ["profession_skills", "free_skills", "subprofession"],
        "background": ["background_skills", "background_attribute_bonuses"],
        "attribute_bases": ["pending_choices", "validation_errors"],
    }.get(field, [])


def apply_dependency_cleanup(creation, changed_field, confirmed=False):
    affected = dependent_fields_for_change(changed_field)
    if affected and not confirmed:
        creation.warnings = [{"field": changed_field, "requires_confirmation": True, "affected": affected}]
        creation.save(update_fields=("warnings", "updated_at"))
        return affected
    if "species_variant" in affected:
        creation.species_variant = None
    if "mixed_species_origins" in affected:
        creation.mixed_species_origins.clear()
    if "ancestry_text" in affected:
        creation.ancestry_text = ""
    if "ancestry_choices" in affected:
        creation.ancestry_choices = {}
    if "species_attribute_bonuses" in affected:
        creation.species_attribute_bonuses = {}
    if "style_skills" in affected:
        creation.style_skills.clear()
    if "favorite_weapon" in affected:
        creation.favorite_weapon = ""
    if "innate_ability" in affected:
        creation.innate_ability = ""
    if "profession_skills" in affected:
        creation.profession_skills.clear()
    if "free_skills" in affected:
        creation.free_skills.clear()
    if "subprofession" in affected:
        creation.subprofession = None
    if "background_skills" in affected:
        creation.background_skills.clear()
    if "background_attribute_bonuses" in affected:
        creation.background_attribute_bonuses = {}
    creation.warnings = []
    creation.save()
    return affected


def adaptive_options(creation):
    return {
        "variants": variants_for_species(creation.species),
        "style_skills": allowed_style_skills(creation.combat_style),
        "profession_skills": allowed_profession_skills(creation.profession),
        "background_skills": allowed_background_skills(creation.background),
        "subprofessions": allowed_subprofessions(creation.profession),
    }
