from django.db import IntegrityError, transaction
from django.utils.text import slugify

from .models import CharacterProficiency, RuleProficiency


def get_skill_proficiency(skill, ruleset_version):
    return RuleProficiency.objects.get(ruleset_version=ruleset_version, slug=f"pericia-{skill.slug}")


def resolve_proficiency_sources(character):
    by_proficiency = {}
    for item in character.rule_proficiencies.select_related("proficiency"):
        current = by_proficiency.get(item.proficiency_id)
        if current is None or item.multiplier > current.multiplier:
            by_proficiency[item.proficiency_id] = item
    return by_proficiency


def add_character_proficiency(character, proficiency, source_type, source_object_id=None, multiplier=1, is_selected=False):
    try:
        with transaction.atomic():
            return CharacterProficiency.objects.create(
                character=character,
                proficiency=proficiency,
                source_type=source_type,
                source_object_id=source_object_id,
                multiplier=multiplier,
                is_selected=is_selected,
            ), False
    except IntegrityError:
        existing = CharacterProficiency.objects.get(
            character=character,
            proficiency=proficiency,
            source_type=source_type,
            source_object_id=source_object_id,
        )
        if multiplier > existing.multiplier:
            existing.multiplier = multiplier
            existing.save(update_fields=("multiplier",))
        return existing, True


def duplicate_skill_names(skills):
    seen, duplicates = set(), []
    for skill in skills:
        if skill.pk in seen:
            duplicates.append(skill.name)
        seen.add(skill.pk)
    return duplicates


def create_static_proficiency(name, category, ruleset_version, source_pages=""):
    return RuleProficiency.objects.update_or_create(
        ruleset_version=ruleset_version,
        slug=f"{category}-{slugify(name)}",
        defaults={"name": name, "category": category, "source_pages": source_pages},
    )[0]
