from .character_calculation_service import ATTRIBUTE_KEYS, INITIAL_ATTRIBUTE_CAP, calculate_attribute_breakdowns, point_distribution_is_valid, standard_array_is_valid


def _skill_names(qs):
    return set(qs.values_list("name", flat=True))


def validate_attribute_bonus_shape(bonuses, source_label):
    total = sum(int(v) for v in bonuses.values())
    if total == 0:
        return [f"{source_label}: bônus de atributo ausente."]
    if total == 2 and sorted([int(v) for v in bonuses.values() if int(v)]) in ([2], [1, 1]):
        if any(key not in ATTRIBUTE_KEYS for key in bonuses):
            return [f"{source_label}: atributo inválido."]
        return []
    return [f"{source_label}: use +2 em um atributo ou +1 em dois atributos diferentes."]


def validate_creation(creation, final=False):
    errors = {}
    pending = []

    if not creation.name:
        pending.append("Nome do personagem")
    if not creation.species:
        errors["species"] = "Escolha uma espécie."
    elif "variant" in creation.species.required_choices and not creation.species_variant:
        errors["species_variant"] = "Esta espécie exige variante."
    if creation.species_variant and creation.species and creation.species_variant.species_id != creation.species_id:
        errors["species_variant"] = "A variante não pertence à espécie selecionada."

    if creation.species and creation.species.slug == "mestico" and creation.mixed_species_origins.count() != 2:
        errors["mixed_species_origins"] = "Mestiço exige duas origens."

    if creation.species and "ancestry" in creation.species.required_choices:
        if not creation.ancestry_text:
            errors["ancestry_text"] = "Informe a ancestralidade."
        common_traits = creation.ancestry_choices.get("common_traits", [])
        specific_traits = creation.ancestry_choices.get("specific_traits", [])
        predator = creation.ancestry_choices.get("predator")
        if predator and (common_traits or specific_traits):
            errors["ancestry_choices"] = "Predador substitui os demais traços de ancestralidade."
        if len(common_traits) > 2 or len(specific_traits) > 1:
            errors["ancestry_choices"] = "Traços Zoan acima do limite permitido."
        if predator and not (creation.ancestry_choices.get("carnivore_hunter") or creation.approved_by_master):
            errors["ancestry_choices"] = "Predador exige ancestral carnívoro caçador ou autorização do mestre."

    if not creation.combat_style:
        errors["combat_style"] = "Escolha um estilo de combate."
    else:
        selected = creation.style_skills.all()
        if selected.count() != creation.combat_style.skill_choice_count:
            errors["style_skills"] = f"Escolha {creation.combat_style.skill_choice_count} perícia(s) do estilo."
        allowed = _skill_names(selected if creation.combat_style.any_skill_allowed else creation.combat_style.allowed_skills)
        invalid = [skill.name for skill in selected if skill.name not in allowed]
        if invalid:
            errors["style_skills_invalid"] = f"Perícias incompatíveis com o estilo: {', '.join(invalid)}."
        if creation.favorite_weapon and creation.favorite_weapon not in creation.combat_style.favorite_weapon_options:
            errors["favorite_weapon"] = "Arma favorita incompatível com o estilo."
        if creation.innate_ability and creation.innate_ability not in creation.combat_style.innate_ability_options:
            errors["innate_ability"] = "Habilidade inata incompatível com o estilo."
        if not creation.favorite_weapon:
            pending.append("Arma favorita")
        if not creation.innate_ability:
            pending.append("Habilidade básica inata")

    if not creation.profession:
        errors["profession"] = "Escolha uma profissão ou Sem Profissão."
    else:
        selected = creation.free_skills.all() if creation.profession.is_no_profession else creation.profession_skills.all()
        if selected.count() != creation.profession.skill_choice_count:
            errors["profession_skills"] = f"Escolha {creation.profession.skill_choice_count} perícia(s) da profissão."
        invalid = [skill.name for skill in selected if skill not in creation.profession.allowed_skills.all()]
        if invalid:
            errors["profession_skills_invalid"] = f"Perícias incompatíveis com a profissão: {', '.join(invalid)}."
        if creation.profession.is_no_profession and creation.subprofession:
            errors["subprofession"] = "Sem Profissão não permite profissão auxiliar."
        if creation.subprofession and creation.subprofession.parent_id != creation.profession_id:
            errors["subprofession"] = "Timoneiro só é permitido para Navegador."

    if not creation.background:
        errors["background"] = "Escolha um antecedente."
    else:
        selected = creation.background_skills.all()
        if selected.count() != creation.background.skill_choice_count:
            errors["background_skills"] = f"Escolha {creation.background.skill_choice_count} perícia(s) do antecedente."
        invalid = [skill.name for skill in selected if skill not in creation.background.allowed_skills.all()]
        if invalid:
            errors["background_skills_invalid"] = f"Perícias incompatíveis com o antecedente: {', '.join(invalid)}."

    if creation.attribute_bases:
        if creation.attribute_method == creation.AttributeMethod.STANDARD_ARRAY and not standard_array_is_valid(creation.attribute_bases):
            errors["attribute_bases"] = "O conjunto padrão deve usar 15, 14, 13, 12, 10 e 8 sem repetir."
        if creation.attribute_method == creation.AttributeMethod.POINT_DISTRIBUTION and not point_distribution_is_valid(creation.attribute_bases):
            errors["attribute_bases"] = "Distribua 72 pontos entre os seis atributos, com mínimo 8 e máximo 15 antes dos bônus."
    elif final:
        errors["attribute_bases"] = "Distribua os atributos."

    errors.update({f"species_bonus_{i}": e for i, e in enumerate(validate_attribute_bonus_shape(creation.species_attribute_bonuses or {}, "Espécie"))})
    if creation.background:
        errors.update({f"background_bonus_{i}": e for i, e in enumerate(validate_attribute_bonus_shape(creation.background_attribute_bonuses or {}, "Antecedente"))})

    for key, values in calculate_attribute_breakdowns(creation).items():
        raw_final = values["base_value"] + values["species_bonus"] + values["background_bonus"] + values["other_bonus"]
        if raw_final > INITIAL_ATTRIBUTE_CAP:
            errors[f"attribute_{key}"] = "Atributo final acima do limite 20."

    chosen_skill_ids = []
    for qs in (creation.style_skills.all(), creation.profession_skills.all(), creation.background_skills.all(), creation.free_skills.all()):
        chosen_skill_ids.extend(qs.values_list("id", flat=True))
    if len(chosen_skill_ids) != len(set(chosen_skill_ids)):
        errors["duplicate_proficiency"] = "Há proficiência repetida em escolhas que exigem nova perícia."

    if pending:
        errors["pending_choices"] = "Escolhas pendentes: " + ", ".join(pending)

    return errors, pending
