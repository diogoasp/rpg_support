from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from campaigns.models import Campaign
from characters.character_calculation_service import (
    ATTRIBUTE_KEYS,
    POINT_DISTRIBUTION_MAX,
    POINT_DISTRIBUTION_MIN,
    POINT_DISTRIBUTION_TOTAL,
    STANDARD_ARRAY,
    calculate_attribute_modifier,
    calculate_attack_bonus,
    calculate_carrying_capacity,
    calculate_damage_bonus,
    calculate_initial_hp,
    calculate_initiative,
    calculate_power_points,
    calculate_resistance_class,
    calculate_saving_throw,
    calculate_skill_bonus,
    calculate_species_training_points,
    derive_mixed_species_values,
    generate_random_attribute_values,
    point_distribution_is_valid,
    remaining_attribute_points,
    standard_array_is_valid,
)
from characters.forms import CharacterCreationAttributesForm, CharacterCreationBackgroundForm, CharacterCreationSpeciesForm
from characters.character_creation_service import confirm_creation, get_or_create_draft
from characters.character_validation_service import validate_creation
from characters.models import (
    Background,
    Character,
    CharacterCreation,
    CharacterRuleException,
    CombatStyle,
    Profession,
    RuleProficiency,
    Skill,
    Species,
    SpeciesVariant,
    ZoanAncestryTrait,
)


def fill_creation(creation, *, species="humano", variant="humano-comum", style="lutador", profession="combatente", background="marinheiro"):
    creation.name = f"{species}-{style}"
    creation.age = "19"
    creation.height = "1,72 m"
    creation.weight = "62 kg"
    creation.dream_path = "freedom_companionship"
    creation.species = Species.objects.get(slug=species)
    if variant:
        creation.species_variant = SpeciesVariant.objects.get(slug=variant)
    creation.combat_style = CombatStyle.objects.get(slug=style)
    creation.profession = Profession.objects.get(slug=profession)
    creation.background = Background.objects.get(slug=background)
    creation.attribute_bases = dict(zip(ATTRIBUTE_KEYS, STANDARD_ARRAY))
    creation.species_attribute_bonuses = {"strength": 2}
    creation.background_attribute_bonuses = {"dexterity": 1, "constitution": 1}
    creation.favorite_weapon = creation.combat_style.favorite_weapon_options[0]
    creation.innate_ability = creation.combat_style.innate_ability_options[0]
    creation.ancestry_choices = {}
    if creation.species.slug == "celestial":
        creation.ancestry_choices["dial"] = "Dial inicial"
    if creation.species.slug in ("mink", "povo-do-mar"):
        creation.ancestry_text = "ancestral coerente"
        creation.ancestry_choices.update({"common_traits": ["visao-agucada"], "specific_traits": []})
    if creation.species_variant:
        required = creation.species_variant.required_choices or []
        if "expert_skill" in required:
            creation.ancestry_choices["expert_skill"] = Skill.objects.filter(is_active=True).first().slug
        if "snake_name" in required:
            creation.ancestry_choices["snake_name"] = "Hebi"
        if "restricted_skill" in required:
            creation.ancestry_choices["restricted_skill"] = "Haki"
        if "marine_ancestry" in required:
            creation.ancestry_choices["marine_ancestry"] = "tubarão"
    creation.save()
    creation.background_skills.set(list(creation.background.allowed_skills.all())[: creation.background.skill_choice_count])
    used = list(creation.background_skills.values_list("id", flat=True))
    style_pool = Skill.objects.filter(is_active=True) if creation.combat_style.any_skill_allowed else creation.combat_style.allowed_skills.all()
    creation.style_skills.set(list(style_pool.exclude(id__in=used))[: creation.combat_style.skill_choice_count])
    used += list(creation.style_skills.values_list("id", flat=True))
    if creation.profession.is_no_profession:
        creation.free_skills.set(list(creation.profession.allowed_skills.exclude(id__in=used))[: creation.profession.skill_choice_count])
    else:
        creation.profession_skills.set(list(creation.profession.allowed_skills.exclude(id__in=used))[: creation.profession.skill_choice_count])
    return creation


class CharacterCreationRulesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_player_book_rules_1_5_7", verbosity=0)
        cls.master = User.objects.create_user("master", role=User.Role.MASTER)
        cls.player = User.objects.create_user("player", password="pass", role=User.Role.PLAYER)
        cls.other = User.objects.create_user("other", role=User.Role.PLAYER)
        cls.campaign = Campaign.objects.create(name="Teste", slug="teste", master=cls.master)
        cls.other_campaign = Campaign.objects.create(name="Outra", slug="outra", master=cls.master)
        cls.campaign.players.add(cls.player)
        cls.other_campaign.players.add(cls.other)

    def test_seed_catalog_is_idempotent_and_complete(self):
        call_command("seed_player_book_rules_1_5_7", verbosity=0)
        self.assertEqual(Species.objects.count(), 8)
        self.assertEqual(CombatStyle.objects.count(), 10)
        self.assertEqual(Profession.objects.filter(parent__isnull=True).count(), 11)
        self.assertEqual(Profession.objects.filter(slug="timoneiro", parent__slug="navegador").count(), 1)
        self.assertEqual(Background.objects.count(), 12)
        self.assertEqual(Skill.objects.filter(related_attribute="presence").count(), 5)
        self.assertEqual(Skill.objects.filter(related_attribute="willpower").count(), 5)
        self.assertEqual(
            set(ZoanAncestryTrait.objects.values_list("name", flat=True)),
            {"Visão Aguçada", "Faro Aguçado", "Garras", "Presas", "Casco ou Carapaça", "Veneno", "Asas", "Predador"},
        )

    def test_each_species_and_variant_is_available(self):
        self.assertEqual(set(Species.objects.values_list("name", flat=True)), {"Anão", "Celestial", "Gigante", "Humano", "Lunariano", "Mestiço", "Mink", "Povo do Mar"})
        self.assertEqual(SpeciesVariant.objects.filter(species__slug="humano").count(), 7)
        self.assertEqual(SpeciesVariant.objects.filter(species__slug="celestial").count(), 3)
        self.assertEqual(SpeciesVariant.objects.filter(species__slug="mink").count(), 3)
        self.assertEqual(SpeciesVariant.objects.filter(species__slug="povo-do-mar").count(), 2)

    def test_calculation_services(self):
        self.assertEqual(calculate_attribute_modifier(8), -1)
        self.assertEqual(calculate_attribute_modifier(15), 2)
        self.assertTrue(standard_array_is_valid(dict(zip(ATTRIBUTE_KEYS, STANDARD_ARRAY))))
        self.assertFalse(standard_array_is_valid(dict(zip(ATTRIBUTE_KEYS, [15, 15, 13, 12, 10, 8]))))
        self.assertEqual(POINT_DISTRIBUTION_TOTAL, 72)
        self.assertEqual(POINT_DISTRIBUTION_MIN, 8)
        self.assertEqual(POINT_DISTRIBUTION_MAX, 15)
        self.assertTrue(point_distribution_is_valid(dict(zip(ATTRIBUTE_KEYS, STANDARD_ARRAY))))
        self.assertFalse(point_distribution_is_valid(dict(zip(ATTRIBUTE_KEYS, [16, 14, 13, 12, 10, 8]))))
        self.assertEqual(remaining_attribute_points(dict(zip(ATTRIBUTE_KEYS, STANDARD_ARRAY))), 0)
        values, rolls = generate_random_attribute_values()
        self.assertEqual(len(values), 6)
        self.assertEqual(len(rolls), 6)
        self.assertEqual(calculate_initial_hp(12, 2, 10), 24)
        self.assertEqual(calculate_power_points(1, 1), 2)
        self.assertEqual(calculate_power_points(1, -2), 0)
        self.assertEqual(calculate_resistance_class(3), 13)
        self.assertEqual(calculate_initiative(3), 3)
        self.assertEqual(calculate_carrying_capacity(15), 150)
        self.assertEqual(calculate_skill_bonus(2, 2, 2), 6)
        self.assertEqual(calculate_saving_throw(1, True), 3)
        self.assertEqual(calculate_attack_bonus(3, True), 5)
        self.assertEqual(calculate_damage_bonus(3), 3)
        self.assertEqual(calculate_species_training_points(-1), 0)
        self.assertEqual(calculate_species_training_points(2), 2)

    def test_mixed_species_values(self):
        humano = Species.objects.get(slug="humano")
        gigante = Species.objects.get(slug="gigante")
        values = derive_mixed_species_values(humano, gigante)
        self.assertEqual(values["base_hp"], 15)
        self.assertEqual(values["movement"], 9)
        self.assertEqual(values["swim_speed"], 4.5)

    def test_validation_rejects_invalid_dependencies(self):
        creation = get_or_create_draft(self.campaign, self.player)
        fill_creation(creation)
        creation.species_variant = SpeciesVariant.objects.get(slug="birkan")
        creation.save()
        errors, _ = validate_creation(creation, final=True)
        self.assertIn("species_variant", errors)

    def test_validation_rejects_invalid_point_distribution(self):
        creation = get_or_create_draft(self.campaign, self.player)
        fill_creation(creation)
        creation.attribute_bases = dict(zip(ATTRIBUTE_KEYS, [15, 14, 13, 12, 10, 9]))
        creation.save()
        errors, _ = validate_creation(creation, final=True)
        self.assertIn("attribute_bases", errors)

    def test_attribute_form_blocks_saving_more_than_72_points(self):
        creation = get_or_create_draft(self.campaign, self.player)
        payload = {"attribute_method": CharacterCreation.AttributeMethod.POINT_DISTRIBUTION}
        payload.update({f"base_{key}": 15 for key in ATTRIBUTE_KEYS})
        form = CharacterCreationAttributesForm(payload, instance=creation)
        self.assertFalse(form.is_valid())
        self.assertIn("72", str(form.errors))

    def test_species_and_background_forms_store_attribute_bonuses_before_attribute_step(self):
        creation = get_or_create_draft(self.campaign, self.player)
        humano = Species.objects.get(slug="humano")
        comum = SpeciesVariant.objects.get(slug="humano-comum")
        species_form = CharacterCreationSpeciesForm(
            {
                "species": humano.pk,
                "species_variant": comum.pk,
                "ancestry_text": "",
                "mixed_species_origins": [],
                "common_ancestry_traits": [],
                "specific_ancestry_traits": [],
                "dial_choice": "",
                "expert_skill": Skill.objects.first().pk,
                "snake_name": "",
                "restricted_skill": "",
                "marine_ancestry": "",
                "species_bonus_mode": "plus1_plus1",
                "species_bonus_primary": "strength",
                "species_bonus_secondary": "dexterity",
            },
            instance=creation,
        )
        self.assertTrue(species_form.is_valid(), species_form.errors)
        species_form.save()
        self.assertEqual(creation.species_attribute_bonuses, {"strength": 1, "dexterity": 1})
        self.assertTrue(creation.ancestry_choices["expert_skill"])

        mestico = Species.objects.get(slug="mestico")
        gigante = Species.objects.get(slug="gigante")
        species_form = CharacterCreationSpeciesForm(
            {
                "species": mestico.pk,
                "species_variant": "",
                "ancestry_text": "",
                "mixed_species_origins": [humano.pk, gigante.pk],
                "common_ancestry_traits": [],
                "specific_ancestry_traits": [],
                "dial_choice": "",
                "expert_skill": "",
                "snake_name": "",
                "restricted_skill": "",
                "marine_ancestry": "",
                "species_bonus_mode": "plus2",
                "species_bonus_primary": "constitution",
                "species_bonus_secondary": "",
            },
            instance=creation,
        )
        self.assertTrue(species_form.is_valid(), species_form.errors)
        species_form.save()
        self.assertEqual(set(creation.mixed_species_origins.values_list("slug", flat=True)), {"humano", "gigante"})

        marinheiro = Background.objects.get(slug="marinheiro")
        background_form = CharacterCreationBackgroundForm(
            {
                "background": marinheiro.pk,
                "background_skills": [skill.pk for skill in marinheiro.allowed_skills.all()[:2]],
                "background_bonus_mode": "plus2",
                "background_bonus_primary": "constitution",
                "background_bonus_secondary": "",
            },
            instance=creation,
        )
        self.assertTrue(background_form.is_valid(), background_form.errors)
        background_form.save()
        self.assertEqual(creation.background_attribute_bonuses, {"constitution": 2})

    def test_mink_species_step_can_save_before_ancestry_is_complete(self):
        user = User.objects.create_user("mink-draft", role=User.Role.PLAYER)
        self.campaign.players.add(user)
        creation = get_or_create_draft(self.campaign, user)
        mink = Species.objects.get(slug="mink")
        robusto = SpeciesVariant.objects.get(slug="robusto")
        species_form = CharacterCreationSpeciesForm(
            {
                "species": mink.pk,
                "species_variant": robusto.pk,
                "ancestry_text": "",
                "mixed_species_origins": [],
                "common_ancestry_traits": [],
                "specific_ancestry_traits": [],
                "dial_choice": "",
                "expert_skill": "",
                "snake_name": "",
                "restricted_skill": "",
                "marine_ancestry": "",
                "species_bonus_mode": "plus2",
                "species_bonus_primary": "dexterity",
                "species_bonus_secondary": "",
            },
            instance=creation,
        )
        self.assertTrue(species_form.is_valid(), species_form.errors)
        species_form.save()
        creation.refresh_from_db()
        self.assertEqual(creation.species, mink)
        self.assertEqual(creation.species_variant, robusto)
        errors, _ = validate_creation(creation, final=True)
        self.assertIn("ancestry_text", errors)

    def test_species_step_saves_mixed_humano_mink_origins(self):
        user = User.objects.create_user("mixed-form", role=User.Role.PLAYER)
        self.campaign.players.add(user)
        mestico = Species.objects.get(slug="mestico")
        humano = Species.objects.get(slug="humano")
        mink = Species.objects.get(slug="mink")
        self.client.force_login(user)
        response = self.client.post(
            f'{reverse("characters:create", kwargs={"slug": self.campaign.slug})}?step=species',
            {
                "step": "species",
                "species": mestico.pk,
                "species_variant": "",
                "mixed_species_origins": [humano.pk, mink.pk],
                "ancestry_text": "",
                "common_ancestry_traits": [],
                "specific_ancestry_traits": [],
                "dial_choice": "",
                "expert_skill": "",
                "snake_name": "",
                "restricted_skill": "",
                "marine_ancestry": "",
                "species_bonus_mode": "plus1_plus1",
                "species_bonus_primary": "wisdom",
                "species_bonus_secondary": "dexterity",
                "next_step": "species",
            },
        )
        self.assertRedirects(response, f'{reverse("characters:create", kwargs={"slug": self.campaign.slug})}?step=species')
        creation = CharacterCreation.objects.get(campaign=self.campaign, user=user)
        self.assertEqual(creation.species, mestico)
        self.assertEqual(set(creation.mixed_species_origins.values_list("slug", flat=True)), {"humano", "mink"})

    def test_species_step_displays_form_errors(self):
        user = User.objects.create_user("species-errors", role=User.Role.PLAYER)
        self.campaign.players.add(user)
        mestico = Species.objects.get(slug="mestico")
        self.client.force_login(user)
        response = self.client.post(
            f'{reverse("characters:create", kwargs={"slug": self.campaign.slug})}?step=species',
            {
                "step": "species",
                "species": mestico.pk,
                "species_variant": "",
                "mixed_species_origins": [],
                "ancestry_text": "",
                "common_ancestry_traits": [],
                "specific_ancestry_traits": [],
                "dial_choice": "",
                "expert_skill": "",
                "snake_name": "",
                "restricted_skill": "",
                "marine_ancestry": "",
                "species_bonus_mode": "plus2",
                "species_bonus_primary": "",
                "species_bonus_secondary": "",
            },
        )
        self.assertEqual(response.status_code, 422)
        self.assertContains(response, "Não foi possível salvar esta etapa", status_code=422)
        self.assertContains(response, "Primeiro atributo", status_code=422)

        response = self.client.post(
            f'{reverse("characters:create", kwargs={"slug": self.campaign.slug})}?step=species',
            {
                "step": "species",
                "species": mestico.pk,
                "species_variant": "",
                "mixed_species_origins": [],
                "ancestry_text": "",
                "common_ancestry_traits": [],
                "specific_ancestry_traits": [],
                "dial_choice": "",
                "expert_skill": "",
                "snake_name": "",
                "restricted_skill": "",
                "marine_ancestry": "",
                "species_bonus_mode": "plus2",
                "species_bonus_primary": "",
                "species_bonus_secondary": "",
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Não foi possível salvar esta etapa")
        self.assertContains(response, "Primeiro atributo")

    def test_no_profession_blocks_subprofession_and_forbidden_skills(self):
        creation = get_or_create_draft(self.campaign, self.player)
        fill_creation(creation, profession="sem-profissao")
        creation.subprofession = Profession.objects.get(slug="timoneiro")
        creation.save()
        creation.free_skills.add(Skill.objects.get(name="Haki"))
        errors, _ = validate_creation(creation, final=True)
        self.assertIn("subprofession", errors)
        self.assertIn("profession_skills_invalid", errors)

    def test_timoneiro_requires_navegador(self):
        creation = get_or_create_draft(self.campaign, self.player)
        fill_creation(creation, profession="combatente")
        creation.subprofession = Profession.objects.get(slug="timoneiro")
        creation.save()
        errors, _ = validate_creation(creation, final=True)
        self.assertIn("subprofession", errors)

    def test_confirmation_creates_character_with_breakdowns_and_origins(self):
        creation = get_or_create_draft(self.campaign, self.player)
        fill_creation(creation, species="humano", variant="humano-comum", style="lutador", profession="combatente", background="marinheiro")
        character = confirm_creation(creation)
        self.assertEqual(character.strength, 17)
        self.assertEqual(character.willpower, 10)
        self.assertEqual(character.presence, 8)
        self.assertEqual(character.max_hp, 24)
        self.assertEqual(character.max_power_points, 1)
        self.assertEqual(character.current_power_points, 1)
        self.assertEqual(character.age, "19")
        self.assertEqual(character.height, "1,72 m")
        self.assertEqual(character.weight, "62 kg")
        self.assertEqual(character.dream_path, "freedom_companionship")
        self.assertEqual(character.attribute_breakdowns.count(), 6)
        self.assertGreater(character.rule_proficiencies.count(), 0)
        self.assertTrue(character.inventory_items.filter(name__icontains="mochila").exists())

    def test_confirmation_creates_missing_static_rule_proficiencies(self):
        user = User.objects.create_user("missing-static-prof", role=User.Role.PLAYER)
        self.campaign.players.add(user)
        creation = fill_creation(get_or_create_draft(self.campaign, user), style="espadachim", profession="arqueologo", background="familia-d")
        creation.combat_style.weapon_proficiencies = ["Armas Cortantes", "Armas Perfurantes"]
        creation.combat_style.save(update_fields=("weapon_proficiencies",))
        RuleProficiency.objects.filter(ruleset_version=creation.ruleset_version, slug="arma-armas-perfurantes").delete()

        character = confirm_creation(creation)

        self.assertTrue(RuleProficiency.objects.filter(ruleset_version=creation.ruleset_version, slug="arma-armas-perfurantes").exists())
        self.assertTrue(character.rule_proficiencies.filter(proficiency__slug="arma-armas-perfurantes").exists())

    def test_species_variant_effects_are_applied_to_final_sheet(self):
        human_user = User.objects.create_user("humanozarrao", role=User.Role.PLAYER)
        self.campaign.players.add(human_user)
        human_creation = fill_creation(get_or_create_draft(self.campaign, human_user), species="humano", variant="humanozarrao")
        human = confirm_creation(human_creation)
        self.assertEqual(human.species, "Humano (Humanozarrão)")
        self.assertTrue(human.features.filter(source="Variante: Humanozarrão", name="size: Grande").exists())
        self.assertTrue(human.features.filter(source="Variante: Humanozarrão", description__icontains="salvaguardas de strength").exists())

        mink_user = User.objects.create_user("mink-robusto", role=User.Role.PLAYER)
        self.campaign.players.add(mink_user)
        mink_creation = fill_creation(get_or_create_draft(self.campaign, mink_user), species="mink", variant="robusto")
        mink = confirm_creation(mink_creation)
        self.assertEqual(mink.species, "Mink (Robusto)")
        self.assertEqual(mink.movement, 12)
        self.assertTrue(mink.features.filter(source="Variante: Robusto", description__icontains="terreno difícil").exists())
        self.assertTrue(mink.features.filter(source__startswith="Ancestralidade:", name="Ancestralidade").exists())

    def test_overlapping_skill_choices_do_not_block_confirmation_or_stack_bonus(self):
        user = User.objects.create_user("overlap", role=User.Role.PLAYER)
        self.campaign.players.add(user)
        creation = fill_creation(get_or_create_draft(self.campaign, user), style="lutador", profession="combatente", background="marinheiro")
        atletismo = Skill.objects.get(name="Atletismo")
        intimidacao = Skill.objects.get(name="Intimidação")
        furtividade = Skill.objects.get(name="Furtividade")
        investigacao = Skill.objects.get(name="Investigação")
        creation.style_skills.set([atletismo, intimidacao])
        creation.profession_skills.set([atletismo, furtividade])
        creation.background_skills.set([atletismo, investigacao])

        errors, _ = validate_creation(creation, final=True)
        self.assertNotIn("duplicate_proficiency", errors)

        character = confirm_creation(creation)
        self.assertEqual(character.skills.filter(skill=atletismo).count(), 1)
        self.assertEqual(character.rule_proficiencies.filter(proficiency__related_skill=atletismo).count(), 3)

    def test_review_post_confirms_character_and_redirects_to_sheet_dashboard(self):
        user = User.objects.create_user("review-ok", role=User.Role.PLAYER)
        self.campaign.players.add(user)
        creation = fill_creation(get_or_create_draft(self.campaign, user))
        self.client.force_login(user)
        response = self.client.post(
            f'{reverse("characters:create", kwargs={"slug": self.campaign.slug})}?step=review',
            {"step": "review", "confirm": "1"},
        )
        self.assertRedirects(response, reverse("characters:dashboard", kwargs={"slug": self.campaign.slug}))
        self.assertTrue(Character.objects.filter(campaign=self.campaign, user=user, name=creation.name).exists())

    def test_review_post_preserves_final_validation_errors(self):
        user = User.objects.create_user("review-error", role=User.Role.PLAYER)
        self.campaign.players.add(user)
        creation = fill_creation(get_or_create_draft(self.campaign, user))
        creation.attribute_bases = dict.fromkeys(ATTRIBUTE_KEYS, 8)
        creation.save()
        self.client.force_login(user)
        response = self.client.post(
            f'{reverse("characters:create", kwargs={"slug": self.campaign.slug})}?step=review',
            {"step": "review", "confirm": "1"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertContains(response, "Não foi possível confirmar a ficha", status_code=422)
        self.assertContains(response, "Distribua 72 pontos", status_code=422)
        self.assertFalse(Character.objects.filter(campaign=self.campaign, user=user).exists())

    def test_master_exception_allows_completion_and_is_recorded(self):
        creation = get_or_create_draft(self.campaign, self.player)
        fill_creation(creation)
        creation.species_attribute_bonuses = {"strength": 3}
        creation.approved_by_master = True
        creation.save()
        CharacterRuleException.objects.create(creation=creation, user=self.master, ignored_rule="bônus racial", justification="teste")
        character = confirm_creation(creation, actor=self.master)
        self.assertEqual(character.creation_state.rule_exceptions.count(), 1)

    def test_htmx_preview_and_permissions_are_campaign_scoped(self):
        self.client.force_login(self.player)
        self.assertEqual(self.client.get(reverse("characters:creation_preview", kwargs={"slug": self.campaign.slug}), HTTP_HX_REQUEST="true").status_code, 200)
        self.assertEqual(self.client.get(reverse("characters:create", kwargs={"slug": self.other_campaign.slug})).status_code, 404)

    def test_creation_wizard_renders_pt_br_labels(self):
        self.client.force_login(self.player)
        response = self.client.get(reverse("characters:create", kwargs={"slug": self.campaign.slug}))
        self.assertContains(response, "Conceito")
        self.assertContains(response, "Idade")
        self.assertContains(response, "Altura")
        self.assertContains(response, "Peso")
        self.assertContains(response, "Caminho")
        self.assertContains(response, "Espécie")
        self.assertContains(response, "Profissão")
        self.assertNotContains(response, ">concept<")

        response = self.client.get(f'{reverse("characters:create", kwargs={"slug": self.campaign.slug})}?step=attributes')
        self.assertContains(response, "Força")
        self.assertContains(response, "Destreza")
        self.assertContains(response, "Constituição")
        self.assertContains(response, "Vontade")
        self.assertContains(response, "Presença")
        self.assertNotContains(response, ">strength<")

    def test_complete_creation_examples(self):
        examples = [
            ("humano", "humano-comum", "lutador", "combatente", "marinheiro"),
            ("mink", "agil", "atirador", "adestrador", "artista"),
            ("povo-do-mar", "homem-peixe", "carateca-homem-peixe", "cozinheiro", "sobrevivente"),
            ("celestial", "birkan", "guerrilheiro", "navegador", "nobre"),
            ("humano", "humano-comum", "ninja", "sem-profissao", "orfao"),
        ]
        for idx, example in enumerate(examples):
            user = User.objects.create_user(f"flow{idx}", role=User.Role.PLAYER)
            self.campaign.players.add(user)
            creation = fill_creation(get_or_create_draft(self.campaign, user), species=example[0], variant=example[1], style=example[2], profession=example[3], background=example[4])
            if creation.species.slug in ("mink", "povo-do-mar"):
                creation.ancestry_text = "ancestral coerente"
                creation.ancestry_choices = {"common_traits": ["visao-agucada"], "specific_traits": []}
                creation.save()
            character = confirm_creation(creation)
            self.assertTrue(Character.objects.filter(pk=character.pk, campaign=self.campaign, user=user).exists())

    def test_complete_mixed_species_requires_two_origins(self):
        user = User.objects.create_user("mixed", role=User.Role.PLAYER)
        self.campaign.players.add(user)
        creation = fill_creation(get_or_create_draft(self.campaign, user), species="mestico", variant=None, style="espadachim", profession="arqueologo", background="familia-d")
        creation.mixed_species_origins.set([Species.objects.get(slug="humano"), Species.objects.get(slug="gigante")])
        character = confirm_creation(creation)
        self.assertIn("Mestiço", character.species)
