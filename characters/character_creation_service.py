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
    Skill,
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


def get_or_create_static_proficiency(creation, slug, name, category):
    return RuleProficiency.objects.get_or_create(
        ruleset_version=creation.ruleset_version,
        slug=slug,
        defaults={"name": name, "category": category},
    )[0]


def apply_catalog_proficiencies(character, creation):
    skill_sources = (
        ("estilo_de_combate", creation.combat_style_id, creation.style_skills.all()),
        ("profissao", creation.profession_id, creation.profession_skills.all()),
        ("antecedente", creation.background_id, creation.background_skills.all()),
        ("sem_profissao", creation.profession_id, creation.free_skills.all()),
    )
    for source_type, source_object_id, skills in skill_sources:
        for skill in skills:
            proficiency = get_skill_proficiency(skill, creation.ruleset_version)
            add_character_proficiency(character, proficiency, source_type, source_object_id, 1, True)
            CharacterSkill.objects.update_or_create(character=character, skill=skill, defaults={"is_proficient": True, "is_expert": False})

    for save in creation.combat_style.saving_throws:
        proficiency = get_or_create_static_proficiency(
            creation,
            f"salvaguarda-{save}",
            f"Salvaguarda de {save}",
            RuleProficiency.Category.SAVING_THROW,
        )
        add_character_proficiency(character, proficiency, "combat_style", creation.combat_style_id, 1, False)

    for weapon in creation.combat_style.weapon_proficiencies:
        proficiency = get_or_create_static_proficiency(
            creation,
            f"arma-{slugify(weapon)}",
            weapon,
            RuleProficiency.Category.WEAPON,
        )
        add_character_proficiency(character, proficiency, "combat_style", creation.combat_style_id, 1, False)

    for kit in creation.combat_style.kit_proficiencies:
        proficiency = get_or_create_static_proficiency(
            creation,
            f"kit-{slugify(kit)}",
            kit,
            RuleProficiency.Category.KIT,
        )
        add_character_proficiency(character, proficiency, "combat_style", creation.combat_style_id, 1, False)


def _set_feature(character, name, source, description, sort_order=0):
    CharacterFeature.objects.update_or_create(
        character=character,
        name=name,
        defaults={"source": source, "description": description, "is_available": True, "sort_order": sort_order},
    )


def _apply_skill_choice(character, creation, skill_slug_or_name, source_type, source_object_id, expert=False):
    skill = Skill.objects.filter(slug=skill_slug_or_name).first() or Skill.objects.filter(name=skill_slug_or_name).first()
    if not skill:
        return
    proficiency = get_skill_proficiency(skill, creation.ruleset_version)
    add_character_proficiency(character, proficiency, source_type, source_object_id, 2 if expert else 1, True)
    current = CharacterSkill.objects.filter(character=character, skill=skill).first()
    CharacterSkill.objects.update_or_create(
        character=character,
        skill=skill,
        defaults={
            "is_proficient": True,
            "is_expert": expert or (current.is_expert if current else False),
            "custom_bonus": current.custom_bonus if current else None,
        },
    )


def _apply_skill_bonus(character, skill_name, bonus):
    skill = Skill.objects.filter(name=skill_name).first()
    if not skill:
        return
    current = CharacterSkill.objects.filter(character=character, skill=skill).first()
    CharacterSkill.objects.update_or_create(
        character=character,
        skill=skill,
        defaults={
            "is_proficient": current.is_proficient if current else False,
            "is_expert": current.is_expert if current else False,
            "custom_bonus": max(current.custom_bonus or 0, int(bonus)) if current else int(bonus),
        },
    )


def _describe_effect(effect):
    kind = effect.get("type")
    if kind == "skill_bonus":
        return f'+{effect["bonus"]} em testes de {effect["skill"]}.'
    if kind == "saving_throw_bonus":
        return f'+{effect["bonus"]} em salvaguardas de {effect["attribute"]}.'
    if kind == "reach":
        return f'Alcance: {effect["text"]}.'
    if kind == "double_skill_choice":
        return f'Escolhe {effect["count"]} perícia para dobrar o bônus de proficiência.'
    if kind == "proficiency_choice":
        return "Escolhe uma proficiência entre: " + ", ".join(effect.get("options", [])) + "."
    if kind == "companion":
        return f'Companheiro: {effect["name"]}.'
    if kind == "zoan_common_choice":
        return f'Escolhe {effect["count"]} Traço Comum de Zoan coerente.'
    if kind == "ignore_difficult_terrain":
        return "Ignora redução por terreno difícil."
    if kind == "swim_dash_bonus_action":
        return "Pode usar Disparada como ação bônus enquanto nada."
    return str(effect)


def apply_species_variant_features(character, creation):
    CharacterFeature.objects.filter(character=character, source__startswith="Espécie:").delete()
    CharacterFeature.objects.filter(character=character, source__startswith="Variante:").delete()
    CharacterFeature.objects.filter(character=character, source__startswith="Ancestralidade:").delete()

    if creation.species:
        source = f"Espécie: {creation.species.name}"
        for index, benefit in enumerate(creation.species.benefits):
            _set_feature(character, benefit, source, "Benefício racial cadastrado pelo catálogo.", 10 + index)
        for index, difficulty in enumerate(creation.species.difficulties):
            _set_feature(character, difficulty, source, "Dificuldade racial cadastrada pelo catálogo.", 30 + index)

    if creation.species_variant:
        source = f"Variante: {creation.species_variant.name}"
        for key, value in creation.species_variant.overrides.items():
            _set_feature(character, f"{key}: {value}", source, "Ajuste de variante aplicado ao personagem.", 40)
        for index, effect in enumerate(creation.species_variant.effects):
            _set_feature(character, f"{creation.species_variant.name} {index + 1}", source, _describe_effect(effect), 50 + index)
            if effect.get("type") == "skill_bonus":
                _apply_skill_bonus(character, effect["skill"], effect["bonus"])

    choices = creation.ancestry_choices or {}
    if choices.get("expert_skill"):
        _apply_skill_choice(character, creation, choices["expert_skill"], "variante", creation.species_variant_id, expert=True)
    if choices.get("restricted_skill"):
        _apply_skill_choice(character, creation, choices["restricted_skill"], "variante", creation.species_variant_id)
    if choices.get("dial"):
        _set_feature(character, "Dial inicial", "Ancestralidade: Celestial", choices["dial"], 60)
    if choices.get("snake_name"):
        _set_feature(character, "Cobra Bélica", "Variante: Kuja", f'Nome: {choices["snake_name"]}.', 60)

    ancestry_parts = []
    if creation.ancestry_text:
        ancestry_parts.append(f"Ancestral: {creation.ancestry_text}.")
    if choices.get("marine_ancestry"):
        ancestry_parts.append(f'Ancestral marinho: {choices["marine_ancestry"]}.')
    if choices.get("common_traits"):
        ancestry_parts.append("Traços comuns: " + ", ".join(choices["common_traits"]) + ".")
    if choices.get("specific_traits"):
        ancestry_parts.append("Traços específicos: " + ", ".join(choices["specific_traits"]) + ".")
    if choices.get("predator"):
        ancestry_parts.append("Predador.")
    if ancestry_parts:
        _set_feature(character, "Ancestralidade", "Ancestralidade: espécie", " ".join(ancestry_parts), 70)


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
    character.max_power_points = derived["max_power_points"]
    character.current_power_points = derived["max_power_points"]
    character.movement = int(creation.species_variant.overrides.get("movement", creation.species.movement) if creation.species_variant else creation.species.movement)
    character.age = creation.age
    character.height = creation.height
    character.weight = creation.weight
    character.dream_path = creation.dream_path
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
    apply_species_variant_features(character, creation)
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
