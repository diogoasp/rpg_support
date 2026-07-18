from .models import Background, CombatStyle, Profession, RULESET_PLAYER_BOOK_1_5_7, Skill, Species, SpeciesVariant, ZoanAncestryTrait


def ruleset_queryset(model, ruleset_version=RULESET_PLAYER_BOOK_1_5_7):
    return model.objects.filter(ruleset_version=ruleset_version, is_active=True)


def get_creation_catalog(ruleset_version=RULESET_PLAYER_BOOK_1_5_7):
    return {
        "species": ruleset_queryset(Species, ruleset_version).prefetch_related("variants"),
        "combat_styles": ruleset_queryset(CombatStyle, ruleset_version).prefetch_related("allowed_skills"),
        "professions": ruleset_queryset(Profession, ruleset_version).filter(parent__isnull=True).prefetch_related("allowed_skills"),
        "subprofessions": ruleset_queryset(Profession, ruleset_version).filter(parent__isnull=False),
        "backgrounds": ruleset_queryset(Background, ruleset_version).prefetch_related("allowed_skills"),
        "skills": Skill.objects.filter(is_active=True),
    }


def variants_for_species(species):
    if not species:
        return SpeciesVariant.objects.none()
    return species.variants.filter(is_active=True)


def allowed_style_skills(style):
    if not style:
        return Skill.objects.none()
    return Skill.objects.filter(is_active=True) if style.any_skill_allowed else style.allowed_skills.filter(is_active=True)


def allowed_profession_skills(profession):
    if not profession:
        return Skill.objects.none()
    return profession.allowed_skills.filter(is_active=True)


def allowed_background_skills(background):
    if not background:
        return Skill.objects.none()
    return background.allowed_skills.filter(is_active=True)


def allowed_subprofessions(profession):
    if not profession:
        return Profession.objects.none()
    return profession.subprofessions.filter(is_active=True)


def zoan_traits_for_ancestry(trait_type=None, predator_allowed=False):
    qs = ZoanAncestryTrait.objects.filter(is_active=True)
    if trait_type:
        qs = qs.filter(trait_type=trait_type)
    if not predator_allowed:
        qs = qs.exclude(trait_type=ZoanAncestryTrait.TraitType.PREDATOR)
    return qs
