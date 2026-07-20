import re

from .models import CANONICAL_ATTRIBUTES, Skill


ATTRIBUTE_LABELS = dict(CANONICAL_ATTRIBUTES) | {
    "intelligence": "Inteligência",
    "charisma": "Carisma",
}


def signed(value):
    value = int(value)
    return f"{value:+d}"


def printable_attribute_rows(character):
    return [
        {
            "key": key,
            "label": label,
            "value": getattr(character, key),
            "modifier": character.attribute_modifier(key),
            "modifier_label": signed(character.attribute_modifier(key)),
        }
        for key, label in CANONICAL_ATTRIBUTES
    ]


def printable_skill_rows(character):
    character_skills = {cs.skill_id: cs for cs in character.skills.select_related("skill").all()}
    rows = []
    for skill in Skill.objects.filter(is_active=True).order_by("name"):
        character_skill = character_skills.get(skill.pk)
        if character_skill:
            bonus = character_skill.final_bonus
            is_proficient = character_skill.is_proficient
            is_expert = character_skill.is_expert
        else:
            bonus = character.attribute_modifier(skill.related_attribute)
            is_proficient = False
            is_expert = False
        rows.append(
            {
                "name": skill.name,
                "attribute": ATTRIBUTE_LABELS.get(skill.related_attribute, skill.get_related_attribute_display()),
                "proficiency": "Especialista" if is_expert else ("Sim" if is_proficient else "Não"),
                "bonus": bonus,
                "bonus_label": signed(bonus),
            }
        )
    return rows


def printable_attack_rows(character):
    rows = [
        {
            "name": "Ataque corpo a corpo",
            "attribute": "Força",
            "die": "1d20",
            "modifier": signed(character.strength_modifier + character.proficiency_bonus),
            "notes": "Use para golpes corporais e armas baseadas em Força quando houver proficiência.",
        },
        {
            "name": "Ataque à distância ou ágil",
            "attribute": "Destreza",
            "die": "1d20",
            "modifier": signed(character.dexterity_modifier + character.proficiency_bonus),
            "notes": "Use para disparos, arremessos e armas baseadas em Destreza quando houver proficiência.",
        },
    ]
    weapon_proficiencies = character.rule_proficiencies.filter(proficiency__category="weapon").select_related("proficiency")
    for character_proficiency in weapon_proficiencies:
        rows.append(
            {
                "name": character_proficiency.proficiency.name,
                "attribute": "Conforme arma",
                "die": "1d20",
                "modifier": f"atributo {signed(character.proficiency_bonus)} prof.",
                "notes": "Proficiência de arma cadastrada para o personagem.",
            }
        )
    return rows


def split_damage_text(damage_text):
    if not damage_text:
        return "Conforme descrição", "Conforme descrição"
    match = re.search(r"(\d+d\d+)([+-]\d+)?", damage_text)
    if not match:
        return damage_text, "Conforme descrição"
    return match.group(1), match.group(2) or "+0"


def printable_technique_rows(character):
    rows = []
    techniques = character.techniques.filter(is_available=True).order_by("sort_order", "name")
    for technique in techniques:
        die, modifier = split_damage_text(technique.damage_text)
        rows.append(
            {
                "name": technique.name,
                "action": technique.get_action_type_display(),
                "attribute": "Conforme técnica",
                "die": die,
                "modifier": modifier,
                "range": technique.range_text or "-",
                "cost": technique.cost or "-",
                "description": technique.description,
                "damage": technique.damage_text,
            }
        )
    return rows


def printable_feature_rows(character):
    return character.features.filter(is_available=True).order_by("sort_order", "name")


def printable_condition_rows(character):
    return character.conditions.filter(is_active=True).order_by("-created_at")


def print_sheet_context(character):
    return {
        "attribute_rows": printable_attribute_rows(character),
        "skill_rows": printable_skill_rows(character),
        "attack_rows": printable_attack_rows(character),
        "technique_rows": printable_technique_rows(character),
        "feature_rows": printable_feature_rows(character),
        "condition_rows": printable_condition_rows(character),
    }
