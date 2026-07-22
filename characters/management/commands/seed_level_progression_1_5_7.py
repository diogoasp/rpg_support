from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from characters.models import (
    BasicAbility,
    CombatStyle,
    CombatStyleLevel,
    CombatStyleLevelFeature,
    CombatStyleTechniqueOption,
    LevelChoiceGroup,
    ProfessionProgression,
    RULESET_PLAYER_BOOK_1_5_7,
)


BASIC_ABILITIES = [
    ("corpo-de-guerreiro", "Corpo de Guerreiro", "general", "Habilidade Básica Geral; inclui progressão de dano desarmado por nível.", {"unarmed_damage_by_level": {"1-5": "1d4", "6-10": "1d6", "11-15": "1d8", "16-20": "1d10"}}),
    ("aprendizado-excepcional", "Aprendizado Excepcional", "general", "Habilidade Básica Geral listada pelo Livro do Jogador.", {}),
    ("aprimoramento-de-atributo", "Aprimoramento de Atributo", "general", "Habilidade Básica Geral listada pelo Livro do Jogador.", {}),
    ("superioridade-absoluta", "Superioridade Absoluta", "general", "Habilidade Básica Geral listada pelo Livro do Jogador.", {}),
    ("perito-em-tecnicas", "Perito em Técnicas", "general", "Habilidade Básica Geral listada pelo Livro do Jogador.", {}),
    ("superando-limites", "Superando Limites", "general", "Habilidade Básica Geral listada pelo Livro do Jogador.", {}),
    ("defesa-ofensiva", "Defesa Ofensiva", "general", "Habilidade Básica Geral listada pelo Livro do Jogador.", {}),
    ("sortudo", "Sortudo", "general", "Habilidade Básica Geral listada pelo Livro do Jogador.", {}),
]

STYLE_FEATURES = {
    "Atirador": {
        2: [("Guarda Astuta", "Reduz riscos do combate; inclui Rompante Defensivo e evoluções posteriores.", {"defensive_reduction": True}, "40")],
        3: [("Atirador de Elite", "Aprimora disparos impossíveis; dobra alcance de técnicas à distância, ignora coberturas e permite penalidade de acerto por dano extra.", {"ranged_attack_upgrade": True}, "40-41")],
        4: [("Queda Suave", "Ao receber dano de queda, reduz o dano em 5 vezes o nível de Atirador.", {"fall_damage_reduction_per_level": 5}, "40"), ("Aumento no Valor de Atributo", "AVA do 4º nível.", {"attribute_increase": True}, "41")],
    },
    "Carateca Homem-Peixe": {
        2: [("Samehada Shotei", "Redireciona ataques corpo a corpo que falham e possui forma alternativa com custo em PP.", {"reaction_redirect_attack": True}, "47")],
        3: [("Jujutsu Homem-Peixe", "Movimentos de controle, arremesso e submissão.", {"choice_group": "Movimentos de Jujutsu"}, "47")],
        4: [("Aumento no Valor de Atributo", "AVA do 4º nível.", {"attribute_increase": True}, "47")],
    },
    "Ciborgue": {
        2: [("Mira Robótica", "Ao errar ataques causa dano parcial e permite usar Sabedoria em jogadas de ataque e dano.", {"wisdom_attack_option": True, "miss_damage": True}, "52")],
        3: [("Guerreiro da Ciência", "Escolha uma tecnologia: Giga-Arm, Mega-Head ou Proto-Body.", {"choice_group": "Guerreiro da Ciência"}, "52-53")],
        4: [("Aumento no Valor de Atributo", "AVA do 4º nível.", {"attribute_increase": True}, "53")],
    },
    "Espadachim": {
        2: [("Consciência Expandida", "Dobra dados contra objetos/estruturas elegíveis e habilita Cortar Mundos.", {"structure_damage_upgrade": True}, "58")],
        3: [("Empunhadura", "Margem crítica 19-20 com arma cortante e escolha entre Lâmina Forte ou Lâmina Gentil.", {"crit_range": "19-20", "choice_group": "Empunhadura"}, "58-59")],
        4: [("Consciência Expandida: Ferro e Carvalho", "A característica se estende a ferro e madeira de carvalho.", {"structure_materials": ["ferro", "madeira de carvalho"]}, "58"), ("Aumento no Valor de Atributo", "AVA do 4º nível.", {"attribute_increase": True}, "59")],
    },
    "Guerreiro-Oni": {
        2: [("Sede de Sangue", "Recupera PV ao reduzir criaturas hostis a 0 PV ou quando aliado o faz após ferimento seu.", {"hp_recovery_on_down": True}, "65")],
        3: [("Saikoro Hakke", "Alterna modos caóticos por 1 minuto com usos por proficiência.", {"random_mode_die": "1d8"}, "65")],
        4: [("Aumento no Valor de Atributo", "AVA do 4º nível.", {"attribute_increase": True}, "65")],
    },
    "Guerrilheiro": {
        2: [("Músculos e Cérebro", "Permite usar Sabedoria em ataques e usa o maior valor entre Força e Sabedoria em testes/salvaguardas.", {"wisdom_attack_option": True}, "71")],
        3: [("Especialista em Combate", "Escolha dois Efeitos Especiais para manipular técnicas.", {"choice_group": "Efeitos Especiais", "choices": 2}, "71")],
        4: [("Aumento no Valor de Atributo", "AVA do 4º nível.", {"attribute_increase": True}, "71")],
    },
    "Lutador": {
        2: [("Bom de Briga", "Benefícios para ataques desarmados, feitos por proficiência e resistência a falhas/críticos.", {"unarmed_upgrade": True}, "76")],
        3: [("Posições de Luta", "Escolha 2 posições de luta.", {"choice_group": "Posições de Luta", "choices": 2}, "76")],
        4: [("Aumento no Valor de Atributo", "AVA do 4º nível.", {"attribute_increase": True}, "76")],
    },
    "Ninja": {
        2: [("Guarda Astuta", "Reduz riscos do combate; inclui Rompante Defensivo e evoluções posteriores.", {"defensive_reduction": True}, "80-81")],
        3: [("Ninjutsu", "Recebe Pontos de Ninjutsu e ações Katon, Doton, Raiton, Suiton e Futon.", {"resource": "PN", "resource_per_level": True}, "81")],
        4: [("Queda Suave", "Ao receber dano de queda, reduz o dano em 5 vezes o nível de Ninja.", {"fall_damage_reduction_per_level": 5}, "80"), ("Aumento no Valor de Atributo", "AVA do 4º nível.", {"attribute_increase": True}, "81")],
    },
    "Okama Kenpo": {
        2: [("Ambiguidade", "Okama Dash, Resistência Okama e Brutalidade Graciosa.", {"movement": 12, "presence_melee_option": True}, "86")],
        3: [("Okama Way", "Gambaray, Poder da Amizade, Super Protetor, Amor Próprio e Amor Insistente.", {"support_feature": True}, "86")],
        4: [("Aumento no Valor de Atributo", "AVA do 4º nível.", {"attribute_increase": True}, "86")],
    },
    "Usuário de Rokushiki": {
        2: [("Espionagem", "Escolha 2 habilidades de espionagem.", {"choice_group": "Espionagem", "choices": 2}, "92-93")],
        3: [("6 Habilidades: Tekkai e Rankyaku", "Aprende Tekkai e Rankyaku pela progressão da característica 6 Habilidades.", {"grant_techniques": ["Tekkai", "Rankyaku"]}, "91-92"), ("Arma Viva", "Escolha 2 características de Arma Viva.", {"choice_group": "Arma Viva", "choices": 2}, "93")],
        4: [("Aumento no Valor de Atributo", "AVA do 4º nível.", {"attribute_increase": True}, "93")],
    },
}

CHOICE_GROUPS = {
    ("Atirador", 3): ("Caminho do Atirador", 1, 1, ["Duelista de Elite", "Sniper de Elite"], "style_path"),
    ("Ciborgue", 3): ("Guerreiro da Ciência", 1, 1, ["Giga-Arm", "Mega-Head", "Proto-Body"], "style_feature"),
    ("Espadachim", 3): ("Empunhadura", 1, 1, ["Lâmina Forte", "Lâmina Gentil"], "style_feature"),
    ("Guerrilheiro", 3): ("Efeitos Especiais", 2, 2, ["Técnica Cirúrgica", "Técnica Distante", "Técnica Escondida", "Técnica Favorável", "Técnica Insistente", "Técnica Otimizada", "Técnica Precavida", "Técnica Veloz"], "style_feature"),
    ("Lutador", 3): ("Posições de Luta", 2, 2, ["Castigo de Ferro", "Descuidado", "Imparável", "Foco de Batalha", "Fanático", "Músculo de Aço"], "style_feature"),
    ("Usuário de Rokushiki", 2): ("Espionagem", 2, 2, ["Aprendizado Rápido", "Ataques Incapacitantes", "Caminho das Sombras", "Infiltrador", "Linguagem de Espião"], "style_feature"),
    ("Usuário de Rokushiki", 3): ("Arma Viva", 2, 2, ["Técnica Assassina", "Execução Impecável", "Fôlego Treinado", "Ataque De Oportunidade Traiçoeiro", "Reação Defensiva", "Habilidades Dominadas"], "style_feature"),
}

LEVEL_3_TECHNIQUES = {
    "Atirador": [("Tiro Certeiro", "combat", 2)],
    "Carateca Homem-Peixe": [("Mawashigeri", "combat", 2)],
    "Ciborgue": [("Metralhadora Portátil", "combat", 2)],
    "Espadachim": [("Trueno Bastardo", "combat", 2)],
    "Guerreiro-Oni": [("Kosanze Ragnaraku", "combat", 2)],
    "Guerrilheiro": [("Great Impact", "combat", 2)],
    "Lutador": [("Power Shoot", "combat", 2)],
    "Ninja": [("Ninpo - Ryuka no Jutsu", "combat", 2)],
    "Okama Kenpo": [("Ballet Chop", "combat", 2)],
    "Usuário de Rokushiki": [("Rankyaku: Hakurai", "combat", 2), ("Tekkai", "auxiliary", 0), ("Rankyaku", "combat", 2)],
}


class Command(BaseCommand):
    help = "Cadastra a progressão de personagens do 1º ao 4º nível para o Livro do Jogador 1.5.7."

    @transaction.atomic
    def handle(self, *args, **options):
        for slug, name, category, description, effects in BASIC_ABILITIES:
            BasicAbility.objects.update_or_create(
                ruleset_version=RULESET_PLAYER_BOOK_1_5_7,
                slug=slug,
                defaults={"name": name, "category": category, "description": description, "effects": effects, "source_pages": "35-38"},
            )

        for level, grade, subdivision in ((1, "Amador", "Novato"), (2, "Amador", "Intermediário"), (3, "Amador", "Veterano"), (4, "Profissional", "Novato")):
            ProfessionProgression.objects.update_or_create(
                ruleset_version=RULESET_PLAYER_BOOK_1_5_7,
                level=level,
                defaults={
                    "grade": grade,
                    "subdivision": subdivision,
                    "grants_professional_feature": level == 4,
                    "feature_name": "Graduação Profissional" if level == 4 else "",
                    "feature_description": "No 4º nível, pode escolher ter vantagem em Teste de Atributo de Perícia Especial do Ofício até 3 vezes por descanso longo." if level == 4 else "",
                },
            )

        for style_name, levels in STYLE_FEATURES.items():
            style = CombatStyle.objects.get(ruleset_version=RULESET_PLAYER_BOOK_1_5_7, name=style_name)
            for level in range(1, 5):
                style_level, _ = CombatStyleLevel.objects.update_or_create(
                    combat_style=style,
                    ruleset_version=RULESET_PLAYER_BOOK_1_5_7,
                    level=level,
                    defaults={
                        "proficiency_bonus": 2,
                        "power_points": level * 2,
                        "hit_die_gain": True,
                        "grants_basic_ability": level in (1, 2, 3),
                        "grants_attribute_increase": level == 4,
                        "grants_techniques": level == 3,
                    },
                )
                CombatStyleLevelFeature.objects.filter(combat_style_level=style_level).delete()
                for sort_order, (name, description, effects, pages) in enumerate(levels.get(level, []), start=1):
                    CombatStyleLevelFeature.objects.create(
                        combat_style_level=style_level,
                        name=name,
                        description=description,
                        reference_text=description,
                        feature_type=CombatStyleLevelFeature.FeatureType.ATTRIBUTE_INCREASE if effects.get("attribute_increase") else CombatStyleLevelFeature.FeatureType.PASSIVE,
                        is_automatic=True,
                        requires_choice=bool(effects.get("choice_group")),
                        choice_group=effects.get("choice_group", ""),
                        effects=effects,
                        source_pages=pages,
                        ruleset_version=RULESET_PLAYER_BOOK_1_5_7,
                        sort_order=sort_order,
                    )
                LevelChoiceGroup.objects.filter(combat_style_level=style_level).delete()
                group = CHOICE_GROUPS.get((style_name, level))
                if group:
                    name, minimum, maximum, allowed, effect_type = group
                    LevelChoiceGroup.objects.create(combat_style_level=style_level, name=name, minimum_choices=minimum, maximum_choices=maximum, allowed_options=allowed, effect_type=effect_type)
                CombatStyleTechniqueOption.objects.filter(combat_style_level=style_level).delete()
                if level == 3:
                    for name, kind, grade in LEVEL_3_TECHNIQUES.get(style_name, []):
                        CombatStyleTechniqueOption.objects.create(
                            combat_style_level=style_level,
                            name=name,
                            technique_kind=kind,
                            grade=grade,
                            source_pages="Cap. 3",
                            ruleset_version=RULESET_PLAYER_BOOK_1_5_7,
                        )

        self.stdout.write(self.style.SUCCESS("Progressão 1-4 do Livro do Jogador 1.5.7 cadastrada/atualizada."))
