from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .character_calculation_service import calculate_attribute_modifier, calculate_initiative, calculate_proficiency_bonus, calculate_resistance_class
from .models import (
    BasicAbility,
    CANONICAL_ATTRIBUTES,
    Character,
    CharacterBasicAbility,
    CharacterFeature,
    CharacterHitPointComponent,
    CharacterLevelUp,
    CharacterLevelUpAuthorization,
    CharacterLevelUpCorrection,
    CharacterLevelUpHistory,
    CharacterTechnique,
    CombatStyle,
    CombatStyleLevel,
    CombatStyleLevelFeature,
    CombatStyleTechniqueOption,
    Profession,
    ProfessionProgression,
    CharacterRecordSource,
    RULESET_PLAYER_BOOK_1_5_7,
)

MAX_IMPLEMENTED_LEVEL = 4
FIXED_HP_VALUES = {8: 5, 10: 6, 12: 7}
STYLE_CATEGORIES = {
    "Carateca Homem-Peixe": BasicAbility.Category.WARRIOR,
    "Lutador": BasicAbility.Category.WARRIOR,
    "Okama Kenpo": BasicAbility.Category.WARRIOR,
    "Usuário de Rokushiki": BasicAbility.Category.WARRIOR,
    "Atirador": BasicAbility.Category.SPECIALIST,
    "Espadachim": BasicAbility.Category.SPECIALIST,
    "Guerreiro-Oni": BasicAbility.Category.WARRIOR,
    "Ciborgue": BasicAbility.Category.DIVERGENT,
    "Guerrilheiro": BasicAbility.Category.DIVERGENT,
    "Ninja": BasicAbility.Category.DIVERGENT,
}
PROFESSION_BY_LEVEL = {
    1: ("Amador", "Novato"),
    2: ("Amador", "Intermediário"),
    3: ("Amador", "Veterano"),
    4: ("Profissional", "Novato"),
}
ATTRIBUTE_KEYS = tuple(key for key, _ in CANONICAL_ATTRIBUTES)


def signed(value):
    value = int(value)
    return f"+{value}" if value >= 0 else str(value)


def calculate_fixed_hp_gain(hit_die, constitution_modifier):
    if int(hit_die) not in FIXED_HP_VALUES:
        raise ValidationError("Dado de Vida sem valor fixo cadastrado para passagem de nível.")
    return max(1, FIXED_HP_VALUES[int(hit_die)] + int(constitution_modifier))


def raw_hp_value(hit_die, method, roll_result=None):
    hit_die = int(hit_die)
    if method == CharacterLevelUp.HpMethod.AVERAGE:
        if hit_die not in FIXED_HP_VALUES:
            raise ValidationError("Dado de Vida sem valor médio cadastrado para passagem de nível.")
        return FIXED_HP_VALUES[hit_die]
    if method == CharacterLevelUp.HpMethod.ROLLED:
        if roll_result is None:
            raise ValidationError("Informe o resultado do Dado de Vida.")
        roll_result = int(roll_result)
        if roll_result < 1 or roll_result > hit_die:
            raise ValidationError(f"Resultado do Dado de Vida deve estar entre 1 e {hit_die}.")
        return roll_result
    raise ValidationError("Método de PV inválido.")


def calculate_hp_gain(hit_die, constitution_modifier, method=CharacterLevelUp.HpMethod.AVERAGE, roll_result=None):
    return max(1, raw_hp_value(hit_die, method, roll_result) + int(constitution_modifier))


def calculate_power_points(level):
    if int(level) < 1 or int(level) > MAX_IMPLEMENTED_LEVEL:
        raise ValidationError("PP desta entrega só está definido para níveis 1 a 4.")
    return int(level) * 2


def apply_constitution_retroactivity(old_modifier, new_modifier, character_level):
    return (int(new_modifier) - int(old_modifier)) * int(character_level)


def _style_for_character(character):
    style = CombatStyle.objects.filter(name=character.combat_style, ruleset_version=RULESET_PLAYER_BOOK_1_5_7, is_active=True).first()
    if not style:
        raise ValidationError({"combat_style": "Estilo de combate do personagem não existe no catálogo 1.5.7."})
    return style


def resolve_style_level_features(character, to_level):
    style = _style_for_character(character)
    try:
        style_level = CombatStyleLevel.objects.prefetch_related("features", "choice_groups", "technique_options").get(
            combat_style=style,
            level=to_level,
            ruleset_version=RULESET_PLAYER_BOOK_1_5_7,
        )
    except CombatStyleLevel.DoesNotExist as exc:
        raise ValidationError({"catalog": f"Progressão de {style.name} nível {to_level} não cadastrada."}) from exc
    if style_level.grants_attribute_increase and to_level != 4:
        raise ValidationError({"catalog": "AVA foi cadastrado fora do 4º nível neste escopo."})
    return style_level


def optional_style_level(character, to_level):
    try:
        return resolve_style_level_features(character, to_level)
    except ValidationError:
        return None


def resolve_profession_progression(character, to_level):
    if character.profession.strip().lower().startswith("sem profissão"):
        return None
    try:
        return ProfessionProgression.objects.get(level=to_level, ruleset_version=RULESET_PLAYER_BOOK_1_5_7)
    except ProfessionProgression.DoesNotExist:
        return None


def get_level_up_requirements(character):
    if character.level >= MAX_IMPLEMENTED_LEVEL:
        raise ValidationError("Passagem acima do 4º nível não está implementada.")
    to_level = character.level + 1
    style = _style_for_character(character)
    style_level = optional_style_level(character, to_level)
    profession_progression = resolve_profession_progression(character, to_level)
    return {
        "from_level": character.level,
        "to_level": to_level,
        "style": style,
        "style_level": style_level,
        "automatic_features": [],
        "choice_groups": [],
        "techniques": [],
        "profession_progression": profession_progression,
        "grants_basic_ability": False,
        "grants_attribute_increase": bool(to_level == 4 or (style_level and style_level.grants_attribute_increase)),
        "favorite_weapon_options": style.favorite_weapon_options,
        "hit_die": style.hit_die,
    }


def validate_master_can_authorize(actor, character):
    if character.campaign.master_id != actor.pk:
        raise PermissionDenied("Somente o mestre da campanha pode autorizar passagem de nível.")


def validate_player_can_execute(actor, character):
    if character.user_id != actor.pk:
        raise PermissionDenied("Somente o dono do personagem pode executar esta passagem de nível.")
    if not character.campaign.players.filter(pk=actor.pk).exists():
        raise PermissionDenied("O jogador não pertence à campanha deste personagem.")


@transaction.atomic
def authorize_level_up(actor, character, master_note=""):
    character = Character.objects.select_for_update().select_related("campaign", "user").get(pk=character.pk)
    validate_master_can_authorize(actor, character)
    if character.level >= MAX_IMPLEMENTED_LEVEL:
        raise ValidationError("Passagem acima do 4º nível não está implementada.")
    if CharacterLevelUpAuthorization.objects.filter(character=character, status__in=[CharacterLevelUpAuthorization.Status.PENDING, CharacterLevelUpAuthorization.Status.IN_PROGRESS]).exists():
        raise ValidationError("Já existe uma autorização pendente ou em andamento para este personagem.")
    requirements = get_level_up_requirements(character)
    authorization = CharacterLevelUpAuthorization(
        character=character,
        campaign=character.campaign,
        authorized_by=actor,
        from_level=character.level,
        to_level=requirements["to_level"],
        master_note=master_note,
        ruleset_version=RULESET_PLAYER_BOOK_1_5_7,
    )
    authorization.full_clean()
    authorization.save()
    return authorization


@transaction.atomic
def cancel_level_up_authorization(actor, authorization):
    authorization = CharacterLevelUpAuthorization.objects.select_for_update().select_related("character__campaign").get(pk=authorization.pk)
    validate_master_can_authorize(actor, authorization.character)
    if authorization.status == CharacterLevelUpAuthorization.Status.COMPLETED:
        raise ValidationError("Autorização concluída não pode ser cancelada.")
    if authorization.status in (CharacterLevelUpAuthorization.Status.CANCELLED, CharacterLevelUpAuthorization.Status.EXPIRED):
        return authorization
    authorization.status = CharacterLevelUpAuthorization.Status.CANCELLED
    authorization.cancelled_at = timezone.now()
    authorization.save(update_fields=("status", "cancelled_at"))
    CharacterLevelUp.objects.filter(authorization=authorization, status=CharacterLevelUp.Status.DRAFT).update(status=CharacterLevelUp.Status.CANCELLED)
    return authorization


def _snapshot(character):
    return {
        "level": character.level,
        "max_hp": character.max_hp,
        "current_hp": character.current_hp,
        "max_power_points": character.max_power_points,
        "current_power_points": character.current_power_points,
        "constitution": character.constitution,
        "proficiency_bonus": character.proficiency_bonus,
        "total_hit_dice": character.total_hit_dice,
        "used_hit_dice": character.used_hit_dice,
        "favorite_weapon": character.favorite_weapon,
        "profession": character.profession,
        "profession_grade": character.profession_grade,
        "profession_subdivision": character.profession_subdivision,
    }


@transaction.atomic
def start_level_up(actor, authorization):
    authorization = CharacterLevelUpAuthorization.objects.select_for_update().select_related("character__campaign").get(pk=authorization.pk)
    character = Character.objects.select_for_update().get(pk=authorization.character_id)
    validate_player_can_execute(actor, character)
    if authorization.status == CharacterLevelUpAuthorization.Status.CANCELLED:
        raise ValidationError("Autorização cancelada.")
    if authorization.status == CharacterLevelUpAuthorization.Status.COMPLETED:
        raise ValidationError("Autorização já concluída.")
    if character.level != authorization.from_level:
        raise ValidationError("O nível atual do personagem diverge da autorização.")
    style = _style_for_character(character)
    process, created = CharacterLevelUp.objects.get_or_create(
        authorization=authorization,
        defaults={
            "character": character,
            "from_level": authorization.from_level,
            "to_level": authorization.to_level,
            "combat_style": style,
            "old_constitution": character.constitution,
            "new_constitution": character.constitution,
            "old_constitution_modifier": character.constitution_modifier,
            "new_constitution_modifier": character.constitution_modifier,
            "old_max_hp": character.max_hp,
            "new_max_hp": character.max_hp,
            "old_max_power_points": character.max_power_points,
            "new_max_power_points": calculate_power_points(authorization.to_level),
            "hp_method": CharacterLevelUp.HpMethod.AVERAGE,
            "snapshot_before": _snapshot(character),
        },
    )
    if authorization.status == CharacterLevelUpAuthorization.Status.PENDING:
        authorization.status = CharacterLevelUpAuthorization.Status.IN_PROGRESS
        authorization.started_at = timezone.now()
        authorization.save(update_fields=("status", "started_at"))
    if created:
        refresh_level_up_preview(process)
    return process


def available_basic_abilities(character, to_level):
    if to_level not in (2, 3):
        return BasicAbility.objects.none()
    owned_ids = CharacterBasicAbility.objects.filter(character=character).values_list("ability_id", flat=True)
    # Imports antigos registravam habilidades passivas somente como CharacterFeature,
    # e nem sempre identificavam a origem como "Habilidade Básica". O nome é o elo
    # disponível nesses registros legados, portanto toda característica ativa com o
    # mesmo nome deve ser considerada uma habilidade já possuída.
    owned_feature_names = CharacterFeature.objects.filter(
        character=character,
        is_available=True,
    ).values_list("name", flat=True)
    category = STYLE_CATEGORIES.get(character.combat_style)
    categories = [BasicAbility.Category.GENERAL]
    if category:
        categories.append(category)
    return (
        BasicAbility.objects.filter(ruleset_version=RULESET_PLAYER_BOOK_1_5_7, is_active=True, category__in=categories)
        .exclude(pk__in=owned_ids)
        .exclude(name__in=owned_feature_names)
        .order_by("category", "name")
    )


def validate_basic_ability_choice(character, to_level, ability):
    if to_level not in (2, 3):
        if ability:
            raise ValidationError("Este nível não concede Habilidade Básica pela regra geral.")
        return None
    if not ability:
        raise ValidationError("Escolha uma Habilidade Básica.")
    if not available_basic_abilities(character, to_level).filter(pk=ability.pk).exists():
        raise ValidationError("Habilidade Básica indisponível, duplicada ou incompatível com o estilo.")
    return ability


def validate_technique_choices(style_level, selected_ids):
    selected_ids = [int(pk) for pk in selected_ids if pk]
    options = list(style_level.technique_options.all())
    required = [option.pk for option in options]
    if style_level.grants_techniques and set(selected_ids) != set(required):
        raise ValidationError("As técnicas obrigatórias previstas para o nível devem ser selecionadas.")
    return list(CombatStyleTechniqueOption.objects.filter(pk__in=selected_ids, combat_style_level=style_level))


TECHNIQUE_DRAFT_FIELDS = ("name","source","description","action_type","range_text","damage_text","damage_die","attribute_modifier","required_weapon_type","power_points_cost","category","technique_type","is_available","is_featured","sort_order")
FEATURE_DRAFT_FIELDS = ("name","source","description","is_available","sort_order")


def source_with_acquired_level(source, to_level):
    text = (source or "").strip() or "Estilo de Combate"
    marker = f"adquirid{'a' if text.lower().startswith(('habilidade','técnica','tecnica','característica','caracteristica')) else 'o'} no nível {to_level}"
    if "adquirid" in text.lower() and f"nível {to_level}" in text.lower():
        return text
    return f"{text} — {marker}"


def validate_level_up_draft_techniques(character, to_level, entries):
    normalized = []
    for index, entry in enumerate(entries or [], start=1):
        data = {field: entry.get(field) for field in TECHNIQUE_DRAFT_FIELDS if field in entry}
        data["name"] = (data.get("name") or "").strip()
        if not data["name"]:
            raise ValidationError(f"Técnica {index}: informe o nome.")
        data["source"] = (data.get("source") or character.combat_style or "Estilo de Combate").strip()
        data["description"] = data.get("description") or ""
        data["action_type"] = data.get("action_type") or "action"
        data["range_text"] = data.get("range_text") or ""
        data["damage_text"] = data.get("damage_text") or ""
        data["damage_die"] = data.get("damage_die") or ""
        data["attribute_modifier"] = data.get("attribute_modifier") or "strength"
        data["required_weapon_type"] = data.get("required_weapon_type") or ""
        data["power_points_cost"] = int(data.get("power_points_cost") or 0)
        data["category"] = data.get("category") or CharacterTechnique.Category.ATTACK
        data["technique_type"] = data.get("technique_type") or CharacterTechnique.TechniqueType.INNATE
        data["is_available"] = bool(data.get("is_available", True))
        data["is_featured"] = bool(data.get("is_featured", False))
        data["sort_order"] = int(data.get("sort_order") or 0)
        candidate = CharacterTechnique(character=character, **data)
        candidate.full_clean(exclude=("source_type","created_by","level_acquired"))
        normalized.append(data)
    return normalized


def validate_level_up_draft_features(character, to_level, entries):
    normalized = []
    for index, entry in enumerate(entries or [], start=1):
        data = {field: entry.get(field) for field in FEATURE_DRAFT_FIELDS if field in entry}
        data["name"] = (data.get("name") or "").strip()
        if not data["name"]:
            raise ValidationError(f"Característica {index}: informe o nome.")
        data["source"] = (data.get("source") or character.combat_style or "Estilo de Combate").strip()
        data["description"] = data.get("description") or ""
        data["is_available"] = bool(data.get("is_available", True))
        data["sort_order"] = int(data.get("sort_order") or 0)
        normalized.append(data)
    return normalized


def validate_attribute_increase(character, to_level, data):
    if to_level != 4:
        return {}
    mode = data.get("mode")
    values = {key: int(data.get(key, 0) or 0) for key in ATTRIBUTE_KEYS}
    total = sum(values.values())
    if not mode and total == 2:
        mode = "plus2" if 2 in values.values() else "plus1_plus1"
    if mode == "plus2":
        if total != 2 or list(values.values()).count(2) != 1:
            raise ValidationError("AVA +2 exige exatamente um atributo com +2.")
    elif mode == "plus1_plus1":
        if total != 2 or list(values.values()).count(1) != 2:
            raise ValidationError("AVA +1/+1 exige dois atributos diferentes com +1.")
    else:
        raise ValidationError("Escolha o formato do AVA.")
    for key, increment in values.items():
        if getattr(character, key) + increment > 20:
            raise ValidationError("AVA não pode elevar atributo acima de 20 neste escopo.")
    return {key: increment for key, increment in values.items() if increment}


def resolve_favorite_weapon(character, keep_current=True, selected_weapon=""):
    style = _style_for_character(character)
    current = character.favorite_weapon
    if keep_current and current:
        return current, False
    selected_weapon = (selected_weapon or "").strip()
    if not selected_weapon:
        selected_weapon = current
    if selected_weapon and selected_weapon not in style.favorite_weapon_options:
        raise ValidationError("Arma favorita incompatível com o Estilo de Combate.")
    return selected_weapon, bool(selected_weapon and selected_weapon != current)


def recalculate_max_hp(character, to_level, new_constitution=None, new_level_fixed_value=None):
    new_constitution = character.constitution if new_constitution is None else int(new_constitution)
    con_mod = calculate_attribute_modifier(new_constitution)
    components = list(character.hp_components.all())
    total = 0
    for component in components:
        if component.source_type == "initial":
            total += component.fixed_hit_die_value + con_mod + component.other_bonus
        elif component.source_type == "level":
            total += component.fixed_hit_die_value + con_mod + component.other_bonus
        else:
            total += component.other_bonus
    if components and new_level_fixed_value is not None:
        total += int(new_level_fixed_value) + con_mod
    if not components:
        if new_level_fixed_value is not None:
            previous_levels = int(to_level) - 1
            retroactive_adjustment = apply_constitution_retroactivity(character.constitution_modifier, con_mod, previous_levels)
            total = int(character.max_hp) + int(new_level_fixed_value) + con_mod + retroactive_adjustment
        else:
            total = int(character.max_hp) + apply_constitution_retroactivity(character.constitution_modifier, con_mod, character.level)
    return max(1, total)


def preview_level_up(process, selected_attribute_increases=None, hp_method=None, hp_roll_result=None):
    character = process.character
    style = process.combat_style
    to_level = process.to_level
    old_con = character.constitution
    increments = selected_attribute_increases or {}
    new_con = old_con + int(increments.get("constitution", 0))
    old_con_mod = character.constitution_modifier
    new_con_mod = calculate_attribute_modifier(new_con)
    method = hp_method or process.hp_method or CharacterLevelUp.HpMethod.AVERAGE
    roll_result = hp_roll_result if hp_roll_result is not None else process.hp_roll_result
    raw_value = raw_hp_value(style.hit_die, method, roll_result)
    hp_gain = calculate_hp_gain(style.hit_die, new_con_mod, method, roll_result)
    new_max_hp = recalculate_max_hp(character, to_level, new_constitution=new_con, new_level_fixed_value=raw_value)
    hp_diff = new_max_hp - character.max_hp
    new_current_hp = min(character.current_hp + hp_diff, new_max_hp) if hp_diff > 0 else min(character.current_hp, new_max_hp)
    new_max_pp = calculate_power_points(to_level)
    pp_diff = new_max_pp - character.max_power_points
    new_current_pp = min(character.current_power_points + pp_diff, new_max_pp)
    return {
        "old_constitution": old_con,
        "new_constitution": new_con,
        "old_constitution_modifier": old_con_mod,
        "new_constitution_modifier": new_con_mod,
        "constitution_retroactive_adjustment": apply_constitution_retroactivity(old_con_mod, new_con_mod, to_level),
        "fixed_hp_value": raw_value,
        "hp_method": method,
        "hp_roll_result": roll_result,
        "hp_gain": hp_gain,
        "old_max_hp": character.max_hp,
        "new_max_hp": new_max_hp,
        "old_current_hp": character.current_hp,
        "new_current_hp": max(0, new_current_hp),
        "old_max_power_points": character.max_power_points,
        "new_max_power_points": new_max_pp,
        "old_current_power_points": character.current_power_points,
        "new_current_power_points": new_current_pp,
        "proficiency_bonus": calculate_proficiency_bonus(to_level),
        "total_hit_dice": to_level,
        "hit_die_type": style.hit_die,
        "favorite_weapon": character.favorite_weapon,
        "favorite_weapon_changed": False,
        "selected_basic_ability": "",
        "attribute_increases": increments,
    }


def refresh_level_up_preview(process):
    preview = preview_level_up(process)
    process.fixed_hp_value = preview["fixed_hp_value"]
    process.hp_method = preview["hp_method"]
    process.hp_roll_result = preview["hp_roll_result"]
    process.hp_gain_total = preview["hp_gain"]
    process.new_constitution = preview["new_constitution"]
    process.old_constitution_modifier = preview["old_constitution_modifier"]
    process.new_constitution_modifier = preview["new_constitution_modifier"]
    process.old_max_hp = preview["old_max_hp"]
    process.new_max_hp = preview["new_max_hp"]
    process.old_max_power_points = preview["old_max_power_points"]
    process.new_max_power_points = preview["new_max_power_points"]
    process.snapshot_after = preview
    process.save(update_fields=("fixed_hp_value","hp_method","hp_roll_result","hp_gain_total","new_constitution","old_constitution_modifier","new_constitution_modifier","old_max_hp","new_max_hp","old_max_power_points","new_max_power_points","snapshot_after"))
    return preview


def save_level_up_draft(actor, process, selected_basic_ability=None, selected_technique_ids=None, selected_attribute_increases=None, selected_style_choices=None, selected_profession_choices=None, keep_favorite_weapon=True, selected_favorite_weapon="", hp_method=None, hp_roll_result=None, draft_techniques=None, draft_features=None):
    validate_player_can_execute(actor, process.character)
    requirements = get_level_up_requirements(process.character)
    if requirements["to_level"] != process.to_level:
        raise ValidationError("O nível atual do personagem diverge do processo.")
    increments = validate_attribute_increase(process.character, process.to_level, selected_attribute_increases or {}) if requirements["grants_attribute_increase"] else {}
    method = hp_method or process.hp_method or CharacterLevelUp.HpMethod.AVERAGE
    roll = hp_roll_result if method == CharacterLevelUp.HpMethod.ROLLED else None
    raw_hp_value(process.combat_style.hit_die, method, roll)
    techniques = validate_level_up_draft_techniques(process.character, process.to_level, draft_techniques if draft_techniques is not None else process.draft_techniques)
    features = validate_level_up_draft_features(process.character, process.to_level, draft_features if draft_features is not None else process.draft_features)
    preview = preview_level_up(process, increments, method, roll)
    process.selected_basic_ability = None
    process.selected_attribute_increases = increments
    process.selected_style_choices = selected_style_choices or {}
    process.selected_profession_choices = selected_profession_choices or {}
    process.selected_favorite_weapon = process.character.favorite_weapon
    process.favorite_weapon_changed = False
    process.hp_method = method
    process.hp_roll_result = roll
    process.hp_gain_total = preview["hp_gain"]
    process.draft_techniques = techniques
    process.draft_features = features
    process.snapshot_after = preview
    process.fixed_hp_value = preview["fixed_hp_value"]
    process.new_constitution = preview["new_constitution"]
    process.new_constitution_modifier = preview["new_constitution_modifier"]
    process.new_max_hp = preview["new_max_hp"]
    process.new_max_power_points = preview["new_max_power_points"]
    process.save()
    process.selected_techniques.clear()
    return process


def _apply_derived_values(character, preview):
    character.level = int(character.level) + 1
    character.proficiency_bonus = preview["proficiency_bonus"]
    character.hit_die_type = preview["hit_die_type"]
    character.total_hit_dice = preview["total_hit_dice"]
    character.max_hp = preview["new_max_hp"]
    character.current_hp = preview["new_current_hp"]
    character.max_power_points = preview["new_max_power_points"]
    character.current_power_points = preview["new_current_power_points"]
    character.armor_class = calculate_resistance_class(character.dexterity_modifier)
    character.initiative = calculate_initiative(character.dexterity_modifier)
    character.favorite_weapon = preview["favorite_weapon"]


@transaction.atomic
def complete_level_up(actor, process):
    process = CharacterLevelUp.objects.select_for_update().select_related("authorization", "character", "combat_style").get(pk=process.pk)
    authorization = CharacterLevelUpAuthorization.objects.select_for_update().get(pk=process.authorization_id)
    character = Character.objects.select_for_update().get(pk=process.character_id)
    validate_player_can_execute(actor, character)
    if authorization.status != CharacterLevelUpAuthorization.Status.IN_PROGRESS:
        raise ValidationError("Autorização não está em andamento.")
    if process.status != CharacterLevelUp.Status.DRAFT:
        raise ValidationError("Processo já concluído ou cancelado.")
    if character.level != authorization.from_level or process.to_level != authorization.to_level:
        raise ValidationError("O nível atual diverge da autorização.")
    requirements = get_level_up_requirements(character)
    increments = validate_attribute_increase(character, process.to_level, process.selected_attribute_increases) if requirements["grants_attribute_increase"] else {}
    draft_techniques = validate_level_up_draft_techniques(character, process.to_level, process.draft_techniques)
    draft_features = validate_level_up_draft_features(character, process.to_level, process.draft_features)
    raw_hp_value(process.combat_style.hit_die, process.hp_method, process.hp_roll_result)
    preview = preview_level_up(process, increments, process.hp_method, process.hp_roll_result)

    for key, increment in increments.items():
        setattr(character, key, getattr(character, key) + increment)
    _apply_derived_values(character, preview)
    progression = requirements["profession_progression"]
    if progression:
        character.profession_grade = progression.grade
        character.profession_subdivision = progression.subdivision
    character.full_clean()
    character.save()

    CharacterHitPointComponent.objects.get_or_create(
        character=character,
        source_type="level",
        source_level=process.to_level,
        defaults={
            "fixed_hit_die_value": preview["fixed_hp_value"],
            "constitution_modifier_at_calculation": preview["new_constitution_modifier"],
            "other_bonus": 0,
        },
    )
    created_techniques = []
    for entry in draft_techniques:
        technique = CharacterTechnique(
            character=character,
            source=source_with_acquired_level(entry.get("source"), process.to_level),
            description=entry.get("description",""),
            name=entry["name"],
            action_type=entry.get("action_type","action"),
            range_text=entry.get("range_text",""),
            damage_text=entry.get("damage_text",""),
            damage_die=entry.get("damage_die",""),
            attribute_modifier=entry.get("attribute_modifier","strength"),
            required_weapon_type=entry.get("required_weapon_type",""),
            power_points_cost=int(entry.get("power_points_cost") or 0),
            category=entry.get("category") or CharacterTechnique.Category.ATTACK,
            technique_type=entry.get("technique_type") or CharacterTechnique.TechniqueType.INNATE,
            is_available=bool(entry.get("is_available",True)),
            is_featured=bool(entry.get("is_featured",False)),
            sort_order=int(entry.get("sort_order") or 0),
            source_type=CharacterRecordSource.LEVEL_UP,
            level_acquired=process.to_level,
            created_by=actor,
        )
        technique.full_clean()
        technique.save()
        created_techniques.append(technique)
    created_features = []
    for entry in draft_features:
        feature = CharacterFeature.objects.create(
            character=character,
            name=entry["name"],
            source=source_with_acquired_level(entry.get("source"), process.to_level),
            description=entry.get("description",""),
            is_available=bool(entry.get("is_available",True)),
            sort_order=int(entry.get("sort_order") or 0),
            source_type=CharacterRecordSource.LEVEL_UP,
            level_acquired=process.to_level,
            created_by=actor,
        )
        created_features.append(feature)

    process.status = CharacterLevelUp.Status.COMPLETED
    process.completed_at = timezone.now()
    process.snapshot_after = preview
    process.favorite_weapon_changed = False
    process.selected_favorite_weapon = character.favorite_weapon
    process.hp_gain_total = preview["hp_gain"]
    process.fixed_hp_value = preview["fixed_hp_value"]
    process.new_constitution = preview["new_constitution"]
    process.new_constitution_modifier = preview["new_constitution_modifier"]
    process.new_max_hp = preview["new_max_hp"]
    process.new_max_power_points = preview["new_max_power_points"]
    process.save()
    authorization.status = CharacterLevelUpAuthorization.Status.COMPLETED
    authorization.completed_at = process.completed_at
    authorization.save(update_fields=("status", "completed_at"))
    history = CharacterLevelUpHistory.objects.create(
        authorization=authorization,
        level_up=process,
        character=character,
        authorized_by=authorization.authorized_by,
        completed_by=actor,
        from_level=process.from_level,
        to_level=process.to_level,
        old_hp=preview["old_current_hp"],
        new_hp=preview["new_current_hp"],
        old_max_hp=preview["old_max_hp"],
        new_max_hp=preview["new_max_hp"],
        fixed_hp_value=preview["fixed_hp_value"],
        constitution_modifier=preview["new_constitution_modifier"],
        constitution_retroactive_adjustment=preview["constitution_retroactive_adjustment"],
        old_power_points=preview["old_current_power_points"],
        new_power_points=preview["new_current_power_points"],
        old_max_power_points=preview["old_max_power_points"],
        new_max_power_points=preview["new_max_power_points"],
        basic_ability=None,
        attribute_increases=increments,
        features_received=[{"name": feature.name, "source": feature.source} for feature in created_features],
        profession_progression={"grade": character.profession_grade, "subdivision": character.profession_subdivision},
        favorite_weapon=character.favorite_weapon,
        hp_method=process.hp_method,
        hp_roll_result=process.hp_roll_result,
        hp_gain_total=preview["hp_gain"],
    )
    history.techniques.clear()
    history.created_techniques.set(created_techniques)
    history.created_features.set(created_features)
    return history


def correct_completed_level_up(actor, history, reason, old_values, new_values):
    if history.character.campaign.master_id != actor.pk:
        raise PermissionDenied("Somente o mestre da campanha pode registrar correção administrativa.")
    return CharacterLevelUpCorrection.objects.create(history=history, reason=reason, old_values=old_values or {}, new_values=new_values or {}, master=actor)
