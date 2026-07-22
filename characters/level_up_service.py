from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

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
    CombatStyle,
    CombatStyleLevel,
    CombatStyleLevelFeature,
    CombatStyleTechniqueOption,
    Profession,
    ProfessionProgression,
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
    "Guerreiro-Oni": BasicAbility.Category.SPECIALIST,
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


def resolve_profession_progression(character, to_level):
    if character.profession.strip().lower().startswith("sem profissão"):
        return None
    try:
        return ProfessionProgression.objects.get(level=to_level, ruleset_version=RULESET_PLAYER_BOOK_1_5_7)
    except ProfessionProgression.DoesNotExist as exc:
        raise ValidationError({"profession": f"Progressão profissional do nível {to_level} não cadastrada."}) from exc


def get_level_up_requirements(character):
    if character.level >= MAX_IMPLEMENTED_LEVEL:
        raise ValidationError("Passagem acima do 4º nível não está implementada.")
    to_level = character.level + 1
    style_level = resolve_style_level_features(character, to_level)
    profession_progression = resolve_profession_progression(character, to_level)
    return {
        "from_level": character.level,
        "to_level": to_level,
        "style": style_level.combat_style,
        "style_level": style_level,
        "automatic_features": list(style_level.features.filter(is_automatic=True)),
        "choice_groups": list(style_level.choice_groups.all()),
        "techniques": list(style_level.technique_options.all()),
        "profession_progression": profession_progression,
        "grants_basic_ability": style_level.grants_basic_ability,
        "grants_attribute_increase": style_level.grants_attribute_increase,
        "favorite_weapon_options": style_level.combat_style.favorite_weapon_options,
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
    owned = CharacterBasicAbility.objects.filter(character=character).values_list("ability_id", flat=True)
    category = STYLE_CATEGORIES.get(character.combat_style)
    categories = [BasicAbility.Category.GENERAL]
    if category:
        categories.append(category)
    return BasicAbility.objects.filter(ruleset_version=RULESET_PLAYER_BOOK_1_5_7, is_active=True, category__in=categories).exclude(pk__in=owned).order_by("category", "name")


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
        hit_die = character.hit_die_type or _style_for_character(character).hit_die
        total += int(hit_die) + con_mod
        for _ in range(2, int(to_level)):
            total += FIXED_HP_VALUES[int(hit_die)] + con_mod
        if new_level_fixed_value is not None:
            total += int(new_level_fixed_value) + con_mod
    return max(1, total)


def preview_level_up(process, selected_basic_ability=None, selected_attribute_increases=None, selected_favorite_weapon=None, keep_favorite_weapon=True):
    character = process.character
    style = process.combat_style
    to_level = process.to_level
    old_con = character.constitution
    increments = selected_attribute_increases or {}
    new_con = old_con + int(increments.get("constitution", 0))
    old_con_mod = character.constitution_modifier
    new_con_mod = calculate_attribute_modifier(new_con)
    fixed_value = FIXED_HP_VALUES[int(style.hit_die)]
    new_max_hp = recalculate_max_hp(character, to_level, new_constitution=new_con, new_level_fixed_value=fixed_value)
    hp_diff = new_max_hp - character.max_hp
    new_current_hp = min(character.current_hp + hp_diff, new_max_hp) if hp_diff > 0 else min(character.current_hp, new_max_hp)
    new_max_pp = calculate_power_points(to_level)
    pp_diff = new_max_pp - character.max_power_points
    new_current_pp = min(character.current_power_points + pp_diff, new_max_pp)
    favorite_weapon, favorite_changed = resolve_favorite_weapon(character, keep_favorite_weapon, selected_favorite_weapon)
    return {
        "old_constitution": old_con,
        "new_constitution": new_con,
        "old_constitution_modifier": old_con_mod,
        "new_constitution_modifier": new_con_mod,
        "constitution_retroactive_adjustment": apply_constitution_retroactivity(old_con_mod, new_con_mod, to_level),
        "fixed_hp_value": fixed_value,
        "hp_gain": calculate_fixed_hp_gain(style.hit_die, new_con_mod),
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
        "favorite_weapon": favorite_weapon,
        "favorite_weapon_changed": favorite_changed,
        "selected_basic_ability": selected_basic_ability.name if selected_basic_ability else "",
        "attribute_increases": increments,
    }


def refresh_level_up_preview(process):
    preview = preview_level_up(process)
    process.fixed_hp_value = preview["fixed_hp_value"]
    process.new_constitution = preview["new_constitution"]
    process.old_constitution_modifier = preview["old_constitution_modifier"]
    process.new_constitution_modifier = preview["new_constitution_modifier"]
    process.old_max_hp = preview["old_max_hp"]
    process.new_max_hp = preview["new_max_hp"]
    process.old_max_power_points = preview["old_max_power_points"]
    process.new_max_power_points = preview["new_max_power_points"]
    process.snapshot_after = preview
    process.save(update_fields=("fixed_hp_value","new_constitution","old_constitution_modifier","new_constitution_modifier","old_max_hp","new_max_hp","old_max_power_points","new_max_power_points","snapshot_after"))
    return preview


def save_level_up_draft(actor, process, selected_basic_ability=None, selected_technique_ids=None, selected_attribute_increases=None, selected_style_choices=None, selected_profession_choices=None, keep_favorite_weapon=True, selected_favorite_weapon=""):
    validate_player_can_execute(actor, process.character)
    requirements = get_level_up_requirements(process.character)
    if requirements["to_level"] != process.to_level:
        raise ValidationError("O nível atual do personagem diverge do processo.")
    ability = validate_basic_ability_choice(process.character, process.to_level, selected_basic_ability)
    techniques = validate_technique_choices(requirements["style_level"], selected_technique_ids or [])
    increments = validate_attribute_increase(process.character, process.to_level, selected_attribute_increases or {}) if requirements["style_level"].grants_attribute_increase else {}
    favorite_weapon, favorite_changed = resolve_favorite_weapon(process.character, keep_favorite_weapon, selected_favorite_weapon)
    preview = preview_level_up(process, ability, increments, favorite_weapon, keep_favorite_weapon=bool(not favorite_changed))
    process.selected_basic_ability = ability
    process.selected_attribute_increases = increments
    process.selected_style_choices = selected_style_choices or {}
    process.selected_profession_choices = selected_profession_choices or {}
    process.selected_favorite_weapon = favorite_weapon
    process.favorite_weapon_changed = favorite_changed
    process.snapshot_after = preview
    process.fixed_hp_value = preview["fixed_hp_value"]
    process.new_constitution = preview["new_constitution"]
    process.new_constitution_modifier = preview["new_constitution_modifier"]
    process.new_max_hp = preview["new_max_hp"]
    process.new_max_power_points = preview["new_max_power_points"]
    process.save()
    process.selected_techniques.set(techniques)
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
    ability = validate_basic_ability_choice(character, process.to_level, process.selected_basic_ability)
    techniques = validate_technique_choices(requirements["style_level"], process.selected_techniques.values_list("pk", flat=True))
    increments = validate_attribute_increase(character, process.to_level, process.selected_attribute_increases) if requirements["style_level"].grants_attribute_increase else {}
    favorite_weapon, favorite_changed = resolve_favorite_weapon(character, keep_current=not process.favorite_weapon_changed, selected_weapon=process.selected_favorite_weapon)
    preview = preview_level_up(process, ability, increments, favorite_weapon, keep_favorite_weapon=not favorite_changed)

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
    if ability:
        CharacterBasicAbility.objects.create(character=character, ability=ability, source_type="level_up", source_level=process.to_level)
        CharacterFeature.objects.update_or_create(
            character=character,
            name=ability.name,
            defaults={"source": f"Habilidade Básica: nível {process.to_level}", "description": ability.description, "is_available": True},
        )
    features_received = []
    for feature in requirements["style_level"].features.all():
        CharacterFeature.objects.update_or_create(
            character=character,
            name=feature.name,
            defaults={"source": f"Estilo {character.combat_style}: nível {process.to_level}", "description": feature.description, "is_available": True, "sort_order": 100 + feature.sort_order},
        )
        features_received.append({"name": feature.name, "type": feature.feature_type, "effects": feature.effects})
    if progression and progression.grants_professional_feature:
        CharacterFeature.objects.update_or_create(
            character=character,
            name=progression.feature_name,
            defaults={"source": f"Profissão: {progression.grade} {progression.subdivision}", "description": progression.feature_description, "is_available": True},
        )

    process.status = CharacterLevelUp.Status.COMPLETED
    process.completed_at = timezone.now()
    process.snapshot_after = preview
    process.favorite_weapon_changed = favorite_changed
    process.selected_favorite_weapon = favorite_weapon
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
        basic_ability=ability,
        attribute_increases=increments,
        features_received=features_received,
        profession_progression={"grade": character.profession_grade, "subdivision": character.profession_subdivision},
        favorite_weapon=favorite_weapon,
    )
    history.techniques.set(techniques)
    return history


def correct_completed_level_up(actor, history, reason, old_values, new_values):
    if history.character.campaign.master_id != actor.pk:
        raise PermissionDenied("Somente o mestre da campanha pode registrar correção administrativa.")
    return CharacterLevelUpCorrection.objects.create(history=history, reason=reason, old_values=old_values or {}, new_values=new_values or {}, master=actor)
