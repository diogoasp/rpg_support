from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.text import slugify
from django.utils import timezone

from .character_calculation_service import preview_derived_values
from .character_validation_service import validate_creation
from .equipment_resolution_service import create_initial_equipment
from .models import (
    Character,
    CharacterAttribute,
    CharacterCreation,
    CharacterFeature,
    CharacterProficiency,
    CharacterSkill,
    RuleProficiency,
)
from .proficiency_resolution_service import add_character_proficiency, get_skill_proficiency


def get_or_create_draft(campaign, user):
    draft = CharacterCreation.objects.filter(campaign=campaign, user=user, status__in=[CharacterCreation.Status.DRAFT, CharacterCreation.Status.READY, CharacterCreation.Status.REOPENED]).first()
    if draft:
        return draft
    return CharacterCreation.objects.create(campaign=campaign, user=user)


def update_validation_state(creation):
    errors, pending = validate_creation(creation)
    creation.validation_errors = errors
    creation.pending_choices = pending
    creation.save(update_fields=("validation_errors", "pending_choices", "updated_at"))
    return errors, pending


def apply_catalog_proficiencies(character, creation):
    for skill in list(creation.style_skills.all()) + list(creation.profession_skills.all()) + list(creation.background_skills.all()) + list(creation.free_skills.all()):
        proficiency = get_skill_proficiency(skill, creation.ruleset_version)
        add_character_proficiency(character, proficiency, "creation_skill_choice", skill.pk, 1, True)
        CharacterSkill.objects.update_or_create(character=character, skill=skill, defaults={"is_proficient": True, "is_expert": False})

    for save in creation.combat_style.saving_throws:
        proficiency = RuleProficiency.objects.get(ruleset_version=creation.ruleset_version, slug=f"salvaguarda-{save}")
        add_character_proficiency(character, proficiency, "combat_style", creation.combat_style_id, 1, False)

    for weapon in creation.combat_style.weapon_proficiencies:
        proficiency = RuleProficiency.objects.get(ruleset_version=creation.ruleset_version, slug=f"arma-{slugify(weapon)}")
        add_character_proficiency(character, proficiency, "combat_style", creation.combat_style_id, 1, False)

    for kit in creation.combat_style.kit_proficiencies:
        proficiency = RuleProficiency.objects.get(ruleset_version=creation.ruleset_version, slug=f"kit-{slugify(kit)}")
        add_character_proficiency(character, proficiency, "combat_style", creation.combat_style_id, 1, False)


@transaction.atomic
def confirm_creation(creation, actor=None):
    errors, pending = validate_creation(creation, final=True)
    if errors and not creation.approved_by_master:
        creation.validation_errors = errors
        creation.pending_choices = pending
        creation.save(update_fields=("validation_errors", "pending_choices", "updated_at"))
        raise ValidationError(errors)

    derived = preview_derived_values(creation)
    attrs = {key: values["final_value"] for key, values in derived["attributes"].items()}
    character = creation.character
    if character is None:
        character = Character(campaign=creation.campaign, user=creation.user)
    character.name = creation.name
    character.level = 1
    character.species = creation.species.name if creation.species else ""
    if creation.species_variant:
        character.species = f"{character.species} ({creation.species_variant.name})"
    character.combat_style = creation.combat_style.name
    character.profession = creation.profession.name
    if creation.subprofession:
        character.profession = f"{character.profession} / {creation.subprofession.name}"
    character.background = creation.background.name
    character.strength = attrs["strength"]
    character.dexterity = attrs["dexterity"]
    character.constitution = attrs["constitution"]
    character.wisdom = attrs["wisdom"]
    character.willpower = attrs["willpower"]
    character.presence = attrs["presence"]
    character.intelligence = 10
    character.charisma = 10
    character.proficiency_bonus = derived["proficiency_bonus"]
    character.armor_class = derived["resistance_class"]
    character.initiative = derived["initiative"]
    character.max_hp = derived["max_hp"]
    character.current_hp = derived["max_hp"]
    character.movement = int(creation.species_variant.overrides.get("movement", creation.species.movement) if creation.species_variant else creation.species.movement)
    character.appearance = creation.appearance
    character.personality = creation.personality
    character.dream = creation.dream
    character.devil_fruit_name = ""
    character.devil_fruit_available = False
    character.full_clean()
    character.save()

    CharacterAttribute.objects.filter(character=character).delete()
    for key, values in derived["attributes"].items():
        CharacterAttribute.objects.create(character=character, attribute=key, **values)

    CharacterProficiency.objects.filter(character=character).delete()
    apply_catalog_proficiencies(character, creation)
    if creation.background:
        CharacterFeature.objects.update_or_create(character=character, name=creation.background.special_feature_name, defaults={"source": f"Antecedente: {creation.background.name}", "description": creation.background.special_feature_description, "is_available": True})
    for feature in creation.combat_style.level_1_features:
        CharacterFeature.objects.update_or_create(character=character, name=feature, defaults={"source": f"Estilo: {creation.combat_style.name}", "description": "Característica de 1º nível cadastrada pelo catálogo.", "is_available": True})

    create_initial_equipment(character, creation)
    creation.character = character
    creation.status = CharacterCreation.Status.COMPLETED
    creation.completed_steps = list(CharacterCreation.STEPS)
    creation.validation_errors = {}
    creation.pending_choices = []
    creation.completed_at = timezone.now()
    creation.save()
    return character
