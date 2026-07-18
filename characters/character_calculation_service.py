import random

from .models import CANONICAL_ATTRIBUTES, CharacterCreation

ATTRIBUTE_KEYS = [key for key, _ in CANONICAL_ATTRIBUTES]
ATTRIBUTE_LABELS = dict(CANONICAL_ATTRIBUTES)
STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]
POINT_DISTRIBUTION_TOTAL = sum(STANDARD_ARRAY)
POINT_DISTRIBUTION_MIN = min(STANDARD_ARRAY)
POINT_DISTRIBUTION_MAX = max(STANDARD_ARRAY)
INITIAL_ATTRIBUTE_CAP = 20


def calculate_attribute_modifier(value):
    return (int(value) - 10) // 2


def roll_4d6_drop_lowest(rng=None):
    rng = rng or random
    rolls = sorted([rng.randint(1, 6) for _ in range(4)])
    return sum(rolls[1:]), rolls


def generate_random_attribute_values(rng=None):
    values, rolls = [], []
    for _ in ATTRIBUTE_KEYS:
        total, rolled = roll_4d6_drop_lowest(rng)
        values.append(total)
        rolls.append(rolled)
    return values, rolls


def calculate_proficiency_bonus(level=1):
    return 2 if level <= 4 else 3 + ((level - 5) // 4)


def compose_attribute_value(base_value, species_bonus=0, background_bonus=0, other_bonus=0, cap=INITIAL_ATTRIBUTE_CAP):
    final = int(base_value) + int(species_bonus) + int(background_bonus) + int(other_bonus)
    return min(final, cap)


def calculate_attribute_breakdowns(creation):
    base = creation.attribute_bases or {}
    species = creation.species_attribute_bonuses or {}
    background = creation.background_attribute_bonuses or {}
    other = creation.other_attribute_bonuses or {}
    return {
        key: {
            "base_value": int(base.get(key, 10)),
            "species_bonus": int(species.get(key, 0)),
            "background_bonus": int(background.get(key, 0)),
            "other_bonus": int(other.get(key, 0)),
            "final_value": compose_attribute_value(base.get(key, 10), species.get(key, 0), background.get(key, 0), other.get(key, 0)),
        }
        for key in ATTRIBUTE_KEYS
    }


def calculate_initial_hp(hit_die, constitution_modifier, species_base_hp, other_modifiers=0):
    return max(1, int(hit_die) + int(constitution_modifier) + int(species_base_hp) + int(other_modifiers))


def calculate_resistance_class(dexterity_modifier, additive_bonus=0, substitute_formula=None):
    if substitute_formula is not None:
        return int(substitute_formula) + int(additive_bonus)
    return 10 + int(dexterity_modifier) + int(additive_bonus)


def calculate_initiative(dexterity_modifier, other_bonus=0):
    return int(dexterity_modifier) + int(other_bonus)


def calculate_carrying_capacity(strength):
    return int(strength) * 10


def calculate_skill_bonus(attribute_modifier, proficiency_bonus=0, multiplier=0, custom_bonus=0):
    return int(attribute_modifier) + (int(proficiency_bonus) * int(multiplier)) + int(custom_bonus)


def calculate_saving_throw(attribute_modifier, is_proficient=False, proficiency_bonus=2, custom_bonus=0):
    return int(attribute_modifier) + (int(proficiency_bonus) if is_proficient else 0) + int(custom_bonus)


def calculate_attack_bonus(attribute_modifier, is_proficient=False, proficiency_bonus=2, custom_bonus=0):
    return int(attribute_modifier) + (int(proficiency_bonus) if is_proficient else 0) + int(custom_bonus)


def calculate_damage_bonus(attribute_modifier, custom_bonus=0):
    return int(attribute_modifier) + int(custom_bonus)


def calculate_species_training_points(wisdom_modifier):
    if wisdom_modifier <= 0:
        return 0
    return max(1, int(wisdom_modifier))


def derive_mixed_species_values(origin_a, origin_b):
    return {
        "base_hp": (origin_a.base_hp + origin_b.base_hp) // 2,
        "size": "Derivado das origens",
        "movement": max(origin_a.movement, origin_b.movement),
        "swim_speed": max(origin_a.swim_speed, origin_b.swim_speed),
        "benefits_required": 2,
        "difficulty_required": 1,
    }


def preview_derived_values(creation):
    breakdowns = calculate_attribute_breakdowns(creation)
    dex_mod = calculate_attribute_modifier(breakdowns["dexterity"]["final_value"])
    con_mod = calculate_attribute_modifier(breakdowns["constitution"]["final_value"])
    str_value = breakdowns["strength"]["final_value"]
    species_hp = 0
    if creation.species:
        species_hp = creation.species.base_hp
        if creation.species.slug == "mestico":
            origins = list(creation.mixed_species_origins.all()[:2])
            if len(origins) == 2:
                species_hp = derive_mixed_species_values(origins[0], origins[1])["base_hp"]
    hit_die = creation.combat_style.hit_die if creation.combat_style else 1
    return {
        "attributes": breakdowns,
        "attribute_rows": [{"key": key, "label": ATTRIBUTE_LABELS[key], **values} for key, values in breakdowns.items()],
        "proficiency_bonus": calculate_proficiency_bonus(1),
        "max_hp": calculate_initial_hp(hit_die, con_mod, species_hp),
        "resistance_class": calculate_resistance_class(dex_mod),
        "initiative": calculate_initiative(dex_mod),
        "carrying_capacity": calculate_carrying_capacity(str_value),
        "species_training_points": calculate_species_training_points(calculate_attribute_modifier(breakdowns["wisdom"]["final_value"])),
    }


def standard_array_is_valid(attribute_bases):
    values = [int(attribute_bases.get(key, 0)) for key in ATTRIBUTE_KEYS]
    return sorted(values) == sorted(STANDARD_ARRAY)


def point_distribution_is_valid(attribute_bases):
    values = [int(attribute_bases.get(key, 0)) for key in ATTRIBUTE_KEYS]
    return (
        len(values) == len(ATTRIBUTE_KEYS)
        and all(POINT_DISTRIBUTION_MIN <= value <= POINT_DISTRIBUTION_MAX for value in values)
        and sum(values) == POINT_DISTRIBUTION_TOTAL
    )


def remaining_attribute_points(attribute_bases):
    return POINT_DISTRIBUTION_TOTAL - sum(int(attribute_bases.get(key, 0) or 0) for key in ATTRIBUTE_KEYS)
