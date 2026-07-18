from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from characters import rules_data as data
from characters.models import (
    Background,
    CombatStyle,
    Profession,
    RuleAttribute,
    RuleProficiency,
    Skill,
    Species,
    SpeciesVariant,
    ZoanAncestryTrait,
)


def skill_slug(name):
    return slugify(name)


class Command(BaseCommand):
    help = "Cadastra o catálogo idempotente do Livro do Jogador 1.5.7."

    @transaction.atomic
    def handle(self, *args, **options):
        version = data.RULESET_VERSION
        for order, (key, name) in enumerate(data.ATTRIBUTES):
            RuleAttribute.objects.update_or_create(
                ruleset_version=version,
                slug=key,
                defaults={"key": key, "name": name, "source_pages": "9-10", "description": "Atributo canônico do OP RPG."},
            )

        skills = {}
        for order, (name, attribute) in enumerate(data.SKILLS):
            skill, _ = Skill.objects.update_or_create(
                slug=skill_slug(name),
                defaults={"name": name, "related_attribute": attribute, "sort_order": order, "is_active": True},
            )
            skills[name] = skill
            RuleProficiency.objects.update_or_create(
                ruleset_version=version,
                slug=f"pericia-{skill.slug}",
                defaults={"name": name, "category": RuleProficiency.Category.SKILL, "related_skill": skill, "source_pages": "226-234"},
            )

        species_by_slug = {}
        for slug, name, hp, size, movement, swim, prejudice, benefits, difficulties, cultures, required, pages in data.SPECIES:
            species, _ = Species.objects.update_or_create(
                ruleset_version=version,
                slug=slug,
                defaults={
                    "name": name,
                    "base_hp": hp,
                    "size": size,
                    "movement": movement,
                    "swim_speed": swim,
                    "prejudice": prejudice,
                    "benefits": benefits,
                    "difficulties": difficulties,
                    "cultural_traits": cultures,
                    "required_choices": required,
                    "source_pages": pages,
                    "description": "Espécie do Capítulo 2 do Livro do Jogador 1.5.7.",
                },
            )
            species_by_slug[slug] = species

        for species_slug, variants in data.VARIANTS.items():
            for slug, name, overrides, effects, required in variants:
                SpeciesVariant.objects.update_or_create(
                    ruleset_version=version,
                    slug=slug,
                    defaults={
                        "species": species_by_slug[species_slug],
                        "name": name,
                        "overrides": overrides,
                        "effects": effects,
                        "required_choices": required,
                        "source_pages": species_by_slug[species_slug].source_pages,
                    },
                )

        for slug, name, trait_type, carnivore_only in data.ZOAN_TRAITS:
            ZoanAncestryTrait.objects.update_or_create(
                ruleset_version=version,
                slug=slug,
                defaults={
                    "name": name,
                    "trait_type": trait_type,
                    "carnivore_hunter_only": carnivore_only,
                    "requires_master_approval": trait_type != "common",
                    "source_pages": "Cap. 6",
                    "description": "Referência a traço Zoan usada somente para ancestralidade.",
                },
            )

        for slug, name, hit_die, saves, count, allowed, weapons, kits, primary, favorite, innate, equipment, money, requirements, features in data.COMBAT_STYLES:
            style, _ = CombatStyle.objects.update_or_create(
                ruleset_version=version,
                slug=slug,
                defaults={
                    "name": name,
                    "hit_die": hit_die,
                    "saving_throws": saves,
                    "skill_choice_count": count,
                    "any_skill_allowed": allowed == "any",
                    "weapon_proficiencies": weapons,
                    "kit_proficiencies": kits,
                    "primary_attributes": primary,
                    "favorite_weapon_options": favorite,
                    "innate_ability_options": innate,
                    "initial_equipment": equipment,
                    "initial_money": money,
                    "requirements": requirements,
                    "level_1_features": features,
                    "source_pages": "31-104",
                },
            )
            style.allowed_skills.set(skills.values() if allowed == "any" else [skills[name] for name in allowed])
            for weapon in weapons:
                RuleProficiency.objects.update_or_create(ruleset_version=version, slug=f"arma-{slugify(weapon)}", defaults={"name": weapon, "category": RuleProficiency.Category.WEAPON, "source_pages": "31-104"})
            for kit in kits:
                RuleProficiency.objects.update_or_create(ruleset_version=version, slug=f"kit-{slugify(kit)}", defaults={"name": kit, "category": RuleProficiency.Category.KIT, "source_pages": "31-104"})
            for save in saves:
                attr_name = dict(data.ATTRIBUTES).get(save, save)
                RuleProficiency.objects.update_or_create(ruleset_version=version, slug=f"salvaguarda-{save}", defaults={"name": f"Salvaguarda de {attr_name}", "category": RuleProficiency.Category.SAVING_THROW, "source_pages": "31-104"})

        professions = {}
        for slug, name, allowed, special, tools, items, knowledges in data.PROFESSIONS:
            profession, _ = Profession.objects.update_or_create(
                ruleset_version=version,
                slug=slug,
                defaults={
                    "name": name,
                    "skill_choice_count": 2,
                    "special_trade_skill": special,
                    "tools": tools,
                    "initial_items": items,
                    "initial_work_knowledges": knowledges,
                    "source_pages": "105-134",
                },
            )
            profession.allowed_skills.set([skills[name] for name in allowed])
            professions[slug] = profession
            for tool in tools:
                RuleProficiency.objects.update_or_create(ruleset_version=version, slug=f"ferramenta-{slugify(tool)}", defaults={"name": tool, "category": RuleProficiency.Category.TOOL, "source_pages": "105-134"})

        no_slug, no_name, no_features = data.NO_PROFESSION
        no_profession, _ = Profession.objects.update_or_create(
            ruleset_version=version,
            slug=no_slug,
            defaults={
                "name": no_name,
                "is_no_profession": True,
                "skill_choice_count": 2,
                "initial_work_knowledges": no_features,
                "restrictions": {"cannot_acquire_professions_later_without_master": True, "forbidden_skills": ["Haki", "Sobrenatural", "Sorte"]},
                "source_pages": "106-107",
            },
        )
        no_profession.allowed_skills.set([s for n, s in skills.items() if n not in ("Haki", "Sobrenatural", "Sorte")])

        t_slug, t_name, parent_slug, knowledges = data.TIMONEIRO
        timoneiro, _ = Profession.objects.update_or_create(
            ruleset_version=version,
            slug=t_slug,
            defaults={"name": t_name, "parent": professions[parent_slug], "skill_choice_count": 0, "initial_work_knowledges": knowledges, "restrictions": {"requires_primary_profession": "navegador"}, "source_pages": "133-134"},
        )
        timoneiro.allowed_skills.clear()

        for slug, name, allowed, recommended, feature in data.BACKGROUNDS:
            background, _ = Background.objects.update_or_create(
                ruleset_version=version,
                slug=slug,
                defaults={
                    "name": name,
                    "skill_choice_count": 2,
                    "recommended_attribute": recommended,
                    "special_feature_name": feature,
                    "special_feature_description": "Característica especial do antecedente; uso narrativo resolvido pelo mestre.",
                    "source_pages": "144-147",
                },
            )
            background.allowed_skills.set([skills[name] for name in allowed])

        self.stdout.write(self.style.SUCCESS("Catálogo do Livro do Jogador 1.5.7 cadastrado/atualizado."))
