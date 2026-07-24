from django.core.management.base import BaseCommand
from django.db import transaction

from characters.models import BasicAbility, RULESET_PLAYER_BOOK_1_5_7


BASIC_ABILITIES = [
    ("aprendizado-excepcional", "Aprendizado Excepcional", "general", "Permite escolher uma Habilidade Básica de uma categoria de Estilo de Combate diferente da categoria do personagem.", {}),
    ("aprimoramento-de-atributo", "Aprimoramento de Atributo", "general", "Aumenta um atributo em 2 ou dois atributos em 1 cada, sem elevar um atributo acima de 20.", {}),
    ("concentracao-inabalavel", "Concentração Inabalável", "general", "Garante sucesso no primeiro teste para manter concentração, +2 no segundo e aprimoramentos nos níveis 5 e 10.", {}),
    ("corpo-de-guerreiro", "Corpo de Guerreiro", "general", "Aprimora ataques desarmados e concede Defesa Aprimorada quando seus requisitos são atendidos.", {"unarmed_damage_by_level": {"1-5": "1d4", "6-10": "1d6", "11-15": "1d8", "16-20": "1d10"}}),
    ("dificuldade-inefavel", "Dificuldade Inefável", "general", "Adiciona metade do bônus de proficiência, arredondada para baixo, à CD de Salvaguardas impostas por técnicas ou características.", {}),
    ("perito-em-tecnicas", "Perito em Técnicas", "general", "Permite não gastar PP quando uma técnica erra ou não afeta criaturas, com usos iguais ao bônus de proficiência.", {}),
    ("preparacao-para-a-batalha", "Preparação para a Batalha", "general", "Com uma ação bônus, inicia um ritual de 1 minuto que estabelece metade do dano máximo como mínimo e auxilia dano ou cura de técnicas.", {}),
    ("prodigio-do-combate", "Prodígio do Combate", "general", "Concede Ataque de Oportunidade, margem de crítico 19-20 para a modalidade escolhida e benefícios contra criaturas de CR superior.", {}),
    ("superioridade-absoluta", "Superioridade Absoluta", "general", "Finaliza criaturas cujos PV restantes sejam iguais ou inferiores ao nível do personagem e amplia temporariamente esse limite.", {}),
    ("superando-limites", "Superando Limites", "general", "Ao iniciar um encontro sem PP, recupera PP conforme o nível e a proficiência ou evita Exaustão de Sobrecarga.", {}),
    ("sortudo", "Sortudo", "general", "Permite refazer uma jogada de ataque, Perícia ou Salvaguarda, com três usos por descanso longo.", {}),
    ("mente-e-corpo", "Mente e Corpo", "warrior", "Com uma ação bônus, ignora temporariamente os efeitos dos cinco primeiros níveis de Exaustão, com três usos por descanso longo.", {}),
    ("retomar-o-folego", "Retomar o Fôlego", "warrior", "Com uma ação bônus, recupera 2d10 PV mais Constituição, com três usos por descanso longo e aprimoramento no 12º nível.", {}),
    ("robusto", "Robusto", "warrior", "Aumenta o máximo de PV em três vezes o nível atual e em mais 3 a cada nível posterior.", {}),
    ("defesa-ofensiva", "Defesa Ofensiva", "specialist", "Permite usar o atributo primário no cálculo da CR e acrescentar parte da proficiência enquanto empunha a arma favorita e atende aos requisitos.", {}),
    ("reflexo-afiado", "Reflexo Afiado", "specialist", "Concede uma ação bônus em cada turno de combate exclusivamente para Disparada, Esconder ou Esquivar.", {}),
    ("gerenciamento-de-energia", "Gerenciamento de Energia", "specialist", "Com uma ação bônus, recupera 1d8 PP mais proficiência, com aprimoramentos no 10º nível.", {}),
]


class Command(BaseCommand):
    help = "Corrige o catálogo usado nas escolhas de Habilidade Básica das passagens para os níveis 2 e 3."

    @transaction.atomic
    def handle(self, *args, **options):
        for slug, name, category, description, effects in BASIC_ABILITIES:
            BasicAbility.objects.update_or_create(
                ruleset_version=RULESET_PLAYER_BOOK_1_5_7,
                slug=slug,
                defaults={
                    "name": name,
                    "category": category,
                    "description": description,
                    "effects": effects,
                    "source_pages": "35-38",
                    "is_active": True,
                    "repeatable": False,
                },
            )

        self.stdout.write(self.style.SUCCESS("Catálogo de Habilidades Básicas da passagem de nível corrigido."))
