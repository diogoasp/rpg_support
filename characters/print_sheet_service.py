import re

from .models import CANONICAL_ATTRIBUTES, CharacterTechnique, Skill


ATTRIBUTE_LABELS = dict(CANONICAL_ATTRIBUTES) | {
    "intelligence": "Inteligência",
    "charisma": "Carisma",
}

SKILL_DESCRIPTION_FALLBACKS = {
    "Acrobacia": "Saltar obstáculos, manter equilíbrio e executar manobras corporais.",
    "Atletismo": "Força física para correr, nadar, escalar, empurrar ou agarrar.",
    "Atuação": "Performance, disfarce cênico, música, dança e presença artística.",
    "Enganação": "Mentir, blefar, disfarçar intenções e sustentar falsas aparências.",
    "Furtividade": "Mover-se sem ser notado, esconder-se e evitar vigilância.",
    "Haki": "Uso e percepção de Haki quando a regra permitir esse tipo de teste.",
    "História": "Conhecimento sobre eventos, povos, lugares, tradições e registros.",
    "Intimidação": "Impor medo, pressão ou ameaça para influenciar alguém.",
    "Intuição": "Ler intenções, emoções, mentiras e pressentir riscos sociais.",
    "Investigação": "Analisar pistas, procurar detalhes e deduzir informações.",
    "Natureza": "Conhecimento de clima, terreno, criaturas, plantas e fenômenos naturais.",
    "Percepção": "Notar sons, movimentos, presenças, detalhes e perigos imediatos.",
    "Persuasão": "Convencer, negociar, inspirar confiança e argumentar.",
    "Prestidigitação": "Truques manuais, furtos discretos, manipulação fina e sabotagem leve.",
    "Provocação": "Irritar, distrair, desafiar ou tirar alguém do eixo.",
    "Sobrenatural": "Entender fenômenos, poderes e efeitos fora do comum.",
    "Sobrevivência": "Rastrear, orientar-se, procurar abrigo, alimento e lidar com perigos naturais.",
    "Sorte": "Resolver situações em que acaso e fortuna são o fator principal.",
}


def signed(value):
    value = int(value)
    return f"{value:+d}"


def attack_test_label(modifier, proficiency_bonus, is_proficient):
    proficiency = int(proficiency_bonus) if is_proficient else 0
    total = int(modifier) + proficiency
    return f"1d20 {signed(total)}"


def unarmed_damage_die(level):
    level = int(level)
    if level <= 5:
        return "1d4"
    if level <= 10:
        return "1d6"
    if level <= 15:
        return "1d8"
    return "1d10"


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
                "description": skill.description or SKILL_DESCRIPTION_FALLBACKS.get(skill.name, "-"),
                "proficiency": "Especialista" if is_expert else ("Sim" if is_proficient else "Não"),
                "bonus": bonus,
                "bonus_label": signed(bonus),
            }
        )
    return rows


def printable_attack_rows(character):
    rows = []
    for weapon in character.weapons.filter(is_available=True).order_by("sort_order", "name"):
        modifier = character.attribute_modifier(weapon.attribute_modifier)
        rows.append(
            {
                "name": f"Ataque básico: {weapon.name}",
                "attribute": ATTRIBUTE_LABELS.get(weapon.attribute_modifier, weapon.get_attribute_modifier_display()),
                "range": weapon.range_text or "-",
                "die": weapon.damage_die or "Conforme arma",
                "modifier": signed(modifier),
                "is_proficient": weapon.is_proficient,
                "attack_test": attack_test_label(modifier, character.proficiency_bonus, weapon.is_proficient),
                "result_label": "Dano",
                "formula": f"{weapon.damage_die or 'dado da arma'} {signed(modifier)}",
                "notes": f"Tipo da arma: {weapon.weapon_type}. O dano usa apenas o modificador do atributo.",
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
        matching_weapons = character.weapons.filter(is_available=True, weapon_type=technique.required_weapon_type).order_by("sort_order", "name") if technique.required_weapon_type else []
        weapon = next(iter(matching_weapons), None)
        row = printable_technique_row(character, technique, weapon)
        row["matching_weapons"] = ", ".join(w.name for w in matching_weapons) if matching_weapons else "-"
        rows.append(row)
    return rows


def printable_technique_row(character, technique, weapon=None):
    modifier_key = "strength" if technique.technique_type == CharacterTechnique.TechniqueType.UNARMED else technique.attribute_modifier
    modifier = character.attribute_modifier(modifier_key)
    modifier_label = signed(modifier)
    is_proficient = bool(weapon and weapon.is_proficient)
    has_configured_die = bool(technique.damage_die or (technique.damage_text and technique.technique_type != CharacterTechnique.TechniqueType.UNARMED))
    technique_die = technique.damage_die or split_damage_text(technique.damage_text)[0]
    weapon_die = weapon.damage_die if weapon else "dado da arma"
    category_label = technique.get_category_display()
    type_label = technique.get_technique_type_display()
    result_label = "Dano"
    if technique.category == CharacterTechnique.Category.SUPPORT and technique.technique_type == CharacterTechnique.TechniqueType.HEAL:
        result_label = "Cura"
    if technique.category == CharacterTechnique.Category.SUPPORT and technique.technique_type == CharacterTechnique.TechniqueType.BUFF:
        result_label = "Buff"

    if technique.technique_type == CharacterTechnique.TechniqueType.UNARMED:
        unarmed_die = unarmed_damage_die(character.level)
        if has_configured_die:
            die = f"{technique_die} + {unarmed_die}"
            formula = f"{technique_die} + {unarmed_die} {signed(character.strength_modifier)}"
        else:
            die = unarmed_die
            formula = f"{unarmed_die} {signed(character.strength_modifier)}"
        attribute = "Força"
        modifier_label = signed(character.strength_modifier)
    elif technique.technique_type == CharacterTechnique.TechniqueType.BASIC:
        die = weapon_die
        formula = f"{weapon_die} {modifier_label}"
        attribute = ATTRIBUTE_LABELS.get(technique.attribute_modifier, technique.get_attribute_modifier_display())
    elif technique.technique_type == CharacterTechnique.TechniqueType.COMBAT:
        die = f"{technique_die} + {weapon_die}"
        formula = f"{technique_die} + {weapon_die} {modifier_label}"
        attribute = ATTRIBUTE_LABELS.get(technique.attribute_modifier, technique.get_attribute_modifier_display())
    elif technique.technique_type == CharacterTechnique.TechniqueType.BUFF:
        die = technique_die
        formula = f"({technique_die} {modifier_label}) / 2"
        attribute = ATTRIBUTE_LABELS.get(technique.attribute_modifier, technique.get_attribute_modifier_display())
    else:
        die = technique_die
        formula = f"{technique_die} {modifier_label}"
        attribute = ATTRIBUTE_LABELS.get(technique.attribute_modifier, technique.get_attribute_modifier_display())

    if technique.technique_type == CharacterTechnique.TechniqueType.BUFF:
        notes = "O resultado dividido por 2 é registrado como bônus de modificador para quem recebeu o buff."
    elif technique.technique_type == CharacterTechnique.TechniqueType.HEAL:
        notes = "Use a mesma fórmula de ataque, mas aplique o resultado como cura."
    else:
        notes = "Some proficiência ao ataque apenas se a técnica ou arma permitir e o personagem for proficiente."

    return {
        "name": technique.name,
        "action": technique.get_action_type_display(),
        "category": category_label,
        "technique_type": type_label,
        "attribute": attribute,
        "range": technique.range_text or "-",
        "die": die,
        "show_result_calculation": not (
            technique.technique_type == CharacterTechnique.TechniqueType.BUFF and not has_configured_die
        ),
        "modifier": modifier_label,
        "is_proficient": is_proficient,
        "attack_test": attack_test_label(modifier, character.proficiency_bonus, is_proficient),
        "formula": formula,
        "result_label": result_label,
        "required_weapon_type": technique.required_weapon_type or "-",
        "cost": technique.power_points_cost if technique.power_points_cost else "-",
        "description": technique.description,
        "damage": technique.damage_text,
        "notes": notes,
    }


def printable_feature_rows(character):
    return character.features.filter(is_available=True).order_by("sort_order", "name")


def split_feature_rows(features):
    positive_rows = []
    limitation_rows = []
    for feature in features:
        if "Defeito" in feature.source or "Limitação" in feature.source or "Dificuldade" in feature.source:
            limitation_rows.append(feature)
        else:
            positive_rows.append(feature)
    return positive_rows, limitation_rows


def printable_condition_rows(character):
    return character.conditions.filter(is_active=True).order_by("-created_at")


def print_sheet_context(character):
    feature_rows = list(printable_feature_rows(character))
    positive_feature_rows, limitation_feature_rows = split_feature_rows(feature_rows)
    return {
        "attribute_rows": printable_attribute_rows(character),
        "skill_rows": printable_skill_rows(character),
        "attack_rows": printable_attack_rows(character),
        "technique_rows": printable_technique_rows(character),
        "feature_rows": feature_rows,
        "positive_feature_rows": positive_feature_rows,
        "limitation_feature_rows": limitation_feature_rows,
        "condition_rows": printable_condition_rows(character),
    }
