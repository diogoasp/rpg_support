RULESET_VERSION = "player-book-1.5.7"

ATTRIBUTES = [
    ("strength", "Força"),
    ("dexterity", "Destreza"),
    ("constitution", "Constituição"),
    ("wisdom", "Sabedoria"),
    ("willpower", "Vontade"),
    ("presence", "Presença"),
]

SKILLS = [
    ("Atletismo", "strength"),
    ("Acrobacia", "dexterity"),
    ("Furtividade", "dexterity"),
    ("Prestidigitação", "dexterity"),
    ("História", "wisdom"),
    ("Investigação", "wisdom"),
    ("Natureza", "wisdom"),
    ("Sobrevivência", "wisdom"),
    ("Atuação", "presence"),
    ("Enganação", "presence"),
    ("Intimidação", "presence"),
    ("Persuasão", "presence"),
    ("Provocação", "presence"),
    ("Haki", "willpower"),
    ("Intuição", "willpower"),
    ("Percepção", "willpower"),
    ("Sobrenatural", "willpower"),
    ("Sorte", "willpower"),
]

SPECIES = [
    ("anao", "Anão", 8, "Miúdo", 9, 4.5, "Débil", ["Corpo Pequeno", "Estômago Pequeno", "Piscar", "Andar das Fadas", "Hóspede Feérico"], ["Ingenuidade Anormal"], ["Pontos de Treinamento por Sabedoria"], [], "15-16"),
    ("celestial", "Celestial", 10, "Médio", 12, 3, "", ["Herança Cultural", "Dials"], [], ["Pontos de Treinamento por Sabedoria"], ["variant", "dial"], "17-18"),
    ("gigante", "Gigante", 20, "Enorme", 9, 3, "", ["Armas gigantescas", "Alcance e tamanho ampliados"], ["Limitações de espaço e equipamentos"], [], [], "19-20"),
    ("humano", "Humano", 10, "Médio", 9, 4.5, "", ["Versatilidade por variante"], [], [], ["variant"], "21-23"),
    ("lunariano", "Lunariano", 16, "Médio", 9, 3, "Perseguição intensa", ["Asas", "Fogo lunariano", "Resistência", "Chama ativa/inativa"], ["Grande preconceito"], [], [], "24-25"),
    ("mestico", "Mestiço", 0, "Derivado", 0, 0, "", ["Benefício de duas origens"], ["Uma dificuldade das origens"], ["Derivado das origens"], ["mixed_origins"], "26-27"),
    ("mink", "Mink", 12, "Pequeno, Médio ou Grande", 9, 4.5, "", ["Electro", "Ancestralidade mamífera"], ["Instintos Animalescos"], [], ["variant", "ancestry"], "27-28"),
    ("povo-do-mar", "Povo do Mar", 14, "Médio ou Grande", 9, 15, "", ["Ancestralidade marinha"], ["Criatura do Mar"], [], ["variant", "ancestry"], "29-30"),
]

VARIANTS = {
    "celestial": [
        ("birkan", "Birkan", {}, [{"type": "skill_bonus", "skill": "Atuação", "bonus": 5}], []),
        ("shandian", "Shandian", {}, [{"type": "skill_bonus", "skill": "Atletismo", "bonus": 5}], []),
        ("skypean", "Skypean", {}, [{"type": "skill_bonus", "skill": "Persuasão", "bonus": 5}], []),
    ],
    "humano": [
        ("humano-comum", "Humano Comum", {}, [{"type": "double_skill_choice", "count": 1}], ["expert_skill"]),
        ("humanozarrao", "Humanozarrão", {"size": "Grande"}, [{"type": "saving_throw_bonus", "attribute": "strength", "bonus": 2}], []),
        ("bracos-longos", "Braços Longos", {}, [{"type": "reach", "text": "3 m com braços"}, {"type": "skill_bonus", "skill": "Prestidigitação", "bonus": 2}], []),
        ("kuja", "Kuja", {}, [{"type": "companion", "name": "Cobra Bélica"}], ["snake_name"]),
        ("pernas-longas", "Pernas Longas", {"movement": 12}, [{"type": "reach", "text": "3 m com pernas"}], []),
        ("pescoco-de-cobra", "Pescoço de Cobra", {}, [{"type": "reach", "text": "3 m com cabeça"}, {"type": "skill_bonus", "skill": "Percepção", "bonus": 2}], []),
        ("tres-olhos", "Três Olhos", {}, [{"type": "proficiency_choice", "options": ["Haki", "Sobrenatural", "Sorte"], "count": 1}], ["restricted_skill"]),
    ],
    "mink": [
        ("agil", "Ágil", {"movement": 12, "climb_speed": 9}, [], []),
        ("meao", "Meão", {"movement": 18}, [], []),
        ("robusto", "Robusto", {"movement": 12}, [{"type": "ignore_difficult_terrain"}], []),
    ],
    "povo-do-mar": [
        ("homem-peixe", "Homem-Peixe", {}, [{"type": "zoan_common_choice", "count": 1}], ["marine_ancestry"]),
        ("sireno", "Sireno", {"swim_speed": 18}, [{"type": "swim_dash_bonus_action"}], ["marine_ancestry"]),
    ],
}

ZOAN_TRAITS = [
    ("visao-agucada", "Visão Aguçada", "common", False),
    ("faro-agucado", "Faro Aguçado", "common", False),
    ("garras", "Garras", "common", False),
    ("presas", "Presas", "common", False),
    ("casco-ou-carapaca", "Casco ou Carapaça", "specific", True),
    ("veneno", "Veneno", "specific", True),
    ("asas", "Asas", "specific", True),
    ("predador", "Predador", "predator", True),
]

COMBAT_STYLES = [
    ("atirador", "Atirador", 8, ["dexterity", "wisdom"], 3, "any", ["Armas de Fogo", "Lançador de Arpão", "Bazuca", "Canhão de Mão", "Armas de Navio"], ["Kit de Abrir Cadeado", "Kit de Escalada", "Kit de Primeiros Socorros"], ["dexterity"], ["Pistola", "Mosquete"], ["Superioridade Absoluta", "Aprendizado Excepcional"], ["2 pistolas", "1 mosquete", "80 munições esféricas"], "5d10 x 1.000 bellys", {}, ["Proficiências do Atirador"]),
    ("carateca-homem-peixe", "Carateca Homem-Peixe", 12, ["constitution", "strength"], 2, ["Acrobacia", "Atletismo", "Atuação", "Intimidação"], ["Armas Marciais", "Tridente"], [], ["strength"], ["Tridente", "Corporal"], ["Corpo de Guerreiro", "Aprimoramento de Atributo"], ["Uma arma marcial", "40.000 bellys"], "15d10 x 1.000 bellys", {"species_or_master_exception": ["povo-do-mar"]}, ["Caratê Homem-Peixe"]),
    ("ciborgue", "Ciborgue", 12, ["strength", "wisdom"], 2, ["Atletismo", "Investigação", "Prestidigitação", "Sobrevivência"], [], [], ["wisdom", "strength"], ["Bazuca", "Canhão de Mão", "Escopeta", "Metralhadora"], ["Aprendizado Excepcional", "Aprimoramento de Atributo"], ["20 unidades de combustível"], "10d10 x 1.000 bellys", {}, ["Corpo Ciborgue"]),
    ("espadachim", "Espadachim", 10, ["dexterity", "willpower"], 2, ["Atletismo", "Intimidação", "Intuição", "Percepção"], ["Armas Cortantes"], [], ["strength", "dexterity"], ["Qualquer arma cortante", "Espada montante"], ["Perito em Técnicas", "Superando Limites"], ["2 sabres", "2 katanas"], "5d10 x 1.000 bellys", {}, ["Postura de Espadachim"]),
    ("guerreiro-oni", "Guerreiro-Oni", 12, ["strength", "constitution"], 2, ["Atletismo", "Intimidação", "Provocação", "Sobrevivência"], ["Kanabo"], [], ["strength"], ["Kanabo", "Machado grande", "Martelo de guerra", "Espada montante", "Corporal"], ["Corpo de Guerreiro", "Superioridade Absoluta"], ["1 kanabo"], "6d10 x 1.000 bellys", {"master_exception": True}, ["Sangue Oni"]),
    ("guerrilheiro", "Guerrilheiro", 10, ["strength", "dexterity"], 2, ["Acrobacia", "Atletismo", "Furtividade", "História", "Sobrevivência"], ["Armas Cortantes", "Armas de Fogo", "Armas Especiais", "Armas Marciais"], ["Kit de Escalada", "Kit de Primeiros Socorros"], ["strength", "wisdom"], ["Qualquer arma", "Corporal"], ["Corpo de Guerreiro", "Aprendizado Excepcional"], ["2 pistolas", "1 mosquete e munição", "2 armas cortantes"], "5d10 x 1.000 bellys", {}, ["Aptidões Bélicas"]),
    ("lutador", "Lutador", 12, ["constitution", "strength"], 2, ["Atletismo", "Intimidação", "Provocação", "Sobrevivência"], ["Armas Marciais"], [], ["strength"], ["Uma arma marcial", "Corporal"], ["Corpo de Guerreiro", "Superando Limites"], ["Uma arma marcial", "40.000 bellys"], "15d10 x 1.000 bellys", {}, ["Posição de Luta"]),
    ("ninja", "Ninja", 8, ["dexterity", "wisdom"], 2, ["Acrobacia", "Enganação", "Furtividade", "Prestidigitação"], ["Katana", "Kunai", "Adaga", "Shuriken", "Foice", "Arco"], ["Kit de Abrir Cadeado", "Kit de Disfarce", "Kit de Escalada", "Kit de Venenos"], ["dexterity"], ["Katana", "Kunai", "Adaga", "Shuriken", "Foice", "Arco"], ["Defesa Ofensiva", "Sortudo"], ["1 katana", "5 kunais", "30 shurikens"], "6d10 x 1.000 bellys", {}, ["Arte Ninja"]),
    ("okama-kenpo", "Okama Kenpo", 10, ["dexterity", "presence"], 3, ["Acrobacia", "Atletismo", "Atuação", "Enganação", "Intimidação", "Intuição", "Provocação"], ["Armas Marciais"], [], ["strength", "presence"], ["Uma arma marcial", "Corporal"], ["Corpo de Guerreiro", "Superando Limites"], ["Uma arma marcial", "40.000 bellys"], "15d10 x 1.000 bellys", {}, ["Protegendo um Amigo"]),
    ("usuario-de-rokushiki", "Usuário de Rokushiki", 10, ["dexterity", "strength"], 2, ["Acrobacia", "Atletismo", "Enganação", "Furtividade", "História", "Investigação"], ["Armas Marciais"], ["Kit de Abrir Cadeado", "Kit de Disfarce", "Kit de Falsificação"], ["strength", "dexterity"], ["Adaga", "Katana", "Bastão", "Corporal"], ["Corpo de Guerreiro", "Perito em Técnicas"], ["Uma arma marcial", "40.000 bellys"], "15d10 x 1.000 bellys", {}, ["Soru e Shigan"]),
]

PROFESSIONS = [
    ("adestrador", "Adestrador", ["Acrobacia", "Atuação", "Intuição", "Percepção", "Persuasão", "Sobrevivência"], "Lidar com Animais", ["Ferramentas de Adestrador"], ["Ferramentas de Adestrador (amador)", "1 mochila pequena", "30 rações para animais"], ["Adestrar Animais", "Vínculo Animal"]),
    ("arqueologo", "Arqueólogo", ["História", "Intuição", "Investigação", "Percepção", "Persuasão", "Sobrevivência"], "História Perdida", ["Ferramentas de Arqueólogo"], ["Ferramentas de Arqueólogo (amador)", "1 mochila pequena", "1 lanterna", "1 corda", "1 tenda"], ["Pesquisa Histórica"]),
    ("cacador-de-recompensas", "Caçador de Recompensas", ["Furtividade", "Intimidação", "Investigação", "Percepção", "Persuasão", "Sobrevivência"], "Caça", ["Ferramentas de Caçador de Recompensas"], ["Ferramentas de Caçador de Recompensas (amador)", "1 mochila pequena"], ["Marca do Caçador"]),
    ("carpinteiro", "Carpinteiro", ["Acrobacia", "Atletismo", "História", "Investigação", "Persuasão", "Prestidigitação"], "Carpintaria", ["Ferramentas de Carpinteiro"], ["Ferramentas de Carpinteiro (amador)", "1 mochila pequena"], ["Construção"]),
    ("combatente", "Combatente", ["Acrobacia", "Atletismo", "Furtividade", "Intimidação", "Provocação", "Sobrevivência"], "Noção de Batalha", ["Ferramentas de Combatente"], ["Ferramentas de Combatente (amador)", "1 mochila pequena"], ["Estratégia"]),
    ("cozinheiro", "Cozinheiro", ["Atuação", "Intuição", "Persuasão", "Prestidigitação", "Provocação", "Sobrevivência"], "Gastronomia", ["Ferramentas de Cozinheiro"], ["Ferramentas de Cozinheiro (amador)", "1 mochila pequena"], ["Preparar Refeição"]),
    ("engenheiro", "Engenheiro", ["História", "Intuição", "Investigação", "Percepção", "Prestidigitação", "Sobrevivência"], "Engenharia", ["Ferramentas de Engenheiro"], ["Ferramentas de Engenheiro (amador)", "1 mochila pequena"], ["Projetar"]),
    ("medico", "Médico", ["História", "Intuição", "Investigação", "Percepção", "Prestidigitação", "Sobrevivência"], "Medicina", ["Ferramentas de Médico"], ["Ferramentas de Médico (amador)", "1 mochila pequena"], ["Tratamento"]),
    ("musico", "Músico", ["Acrobacia", "Atuação", "Enganação", "Furtividade", "Intimidação", "Intuição", "Percepção", "Persuasão", "Prestidigitação", "Provocação"], "Canção", ["Ferramentas de Músico"], ["Ferramentas de Músico (amador)", "1 mochila pequena"], ["Performance"]),
    ("navegador", "Navegador", ["Enganação", "Intuição", "Investigação", "Percepção", "Persuasão", "Sobrevivência"], "Navegação", ["Ferramentas de Navegador"], ["Ferramentas de Navegador (amador)", "1 mochila pequena"], ["Leitura do Clima"]),
]

NO_PROFESSION = ("sem-profissao", "Sem Profissão", ["Ajudante Perfeito", "Foco", "Parceiro de Treino", "Tempo Livre"])
TIMONEIRO = ("timoneiro", "Timoneiro", "navegador", ["Manobra de Leme", "Controle de Navio"])

BACKGROUNDS = [
    ("artista", "Artista", ["Acrobacia", "Atuação", "História", "Persuasão", "Prestidigitação", "Provocação"], "presence", "Rock Star"),
    ("criminoso", "Criminoso", ["Enganação", "Furtividade", "Intimidação", "Prestidigitação"], "dexterity", "Contatos"),
    ("escravo", "Escravo", ["Atletismo", "Intuição", "Percepção", "Sobrevivência"], "constitution", "Esperança"),
    ("familia-d", "Família D.", ["Haki", "Intimidação", "Intuição", "Percepção"], "willpower", "Vontade dos D."),
    ("marinheiro", "Marinheiro", ["Acrobacia", "Atletismo", "Investigação", "Sobrevivência"], "strength", "Carteirada"),
    ("nobre", "Nobre", ["História", "Intuição", "Investigação", "Natureza", "Sorte"], "wisdom", "Influência"),
    ("orfao", "Órfão", ["Atletismo", "Furtividade", "Intuição", "Sobrevivência"], "strength", "Malandragem"),
    ("politico", "Político", ["Atuação", "Enganação", "História", "Intuição", "Persuasão", "Provocação"], "presence", "Discurso"),
    ("revolucionario", "Revolucionário", ["Acrobacia", "Atletismo", "História", "Persuasão"], "dexterity", "Herói do Povo"),
    ("sacerdote", "Sacerdote", ["História", "Percepção", "Persuasão", "Sobrenatural"], "wisdom", "Fiéis"),
    ("sobrevivente", "Sobrevivente", ["História", "Intuição", "Percepção", "Sobrevivência"], "willpower", "Reputação"),
    ("tenryuubito", "Tenryuubito", ["História", "Intimidação", "Investigação", "Natureza"], "constitution", "Costas Quentes"),
]
