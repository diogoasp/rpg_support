# Passagem de nivel assistida 1-4 - OP RPG Livro do Jogador 1.5.7

Fonte normativa exclusiva: `OP RPG - Livro do Jogador 1.5.7.pdf`.

Escopo implementado: transicoes 1 -> 2, 2 -> 3 e 3 -> 4. Nao ha Multiestilo, niveis epicos, troca de Estilo, Akuma no Mi automatica ou desbloqueio automatico de Haki.

## Regras

- O mestre autoriza a passagem; o nivel so muda quando o jogador conclui.
- Ha uma unica autorizacao pendente/em andamento por personagem.
- A autorizacao exige `to_level = from_level + 1` e `to_level <= 4`.
- O bonus de proficiencia permanece `+2` nos niveis 1 a 4.
- PP maximo usa `level * 2`: 2, 4, 6 e 8.
- Ao aumentar PP maximo, o PP atual aumenta apenas pela diferenca do maximo.
- Dado de Vida usa sempre metodo fixo, sem rolagem: d8 = 5, d10 = 6, d12 = 7.
- Cada passagem concede +1 Dado de Vida total do Estilo atual.
- PV atual acompanha aumentos do PV maximo pela diferenca; reducoes limitam o PV atual ao novo maximo.
- Constituicao e recalculada retroativamente quando muda o modificador.
- Habilidade Basica geral/categoria e escolhida no 2o e 3o nivel; nao no 4o.
- AVA no 4o nivel permite +2 em um atributo ou +1/+1 em dois atributos diferentes, ate 20.
- Profissao evolui: 1 Amador/Novato, 2 Amador/Intermediario, 3 Amador/Veterano, 4 Profissional/Novato.
- Sem Profissao nao recebe progressao profissional.
- Arma favorita pode ser mantida ou refeita entre as opcoes do Estilo.

## Catalogo

O comando `seed_level_progression_1_5_7` cadastra:

- `CombatStyleLevel` dos niveis 1 a 4 para os 10 Estilos cadastrados.
- `CombatStyleLevelFeature` dos niveis 2, 3 e 4.
- grupos de escolha estruturados quando o texto do Estilo exige escolha.
- tecnicas predefinidas de 3o nivel localizadas nas tabelas do Capitulo 3.
- `BasicAbility` para opcoes usadas pelo catalogo atual.
- `ProfessionProgression` dos niveis 1 a 4.

## Models

- `CharacterLevelUpAuthorization`: autorizacao do mestre, status e auditoria.
- `CharacterLevelUp`: processo/rascunho do jogador, escolhas principais e snapshots.
- `CharacterLevelUpHistory`: registro imutavel da conclusao.
- `CharacterLevelUpCorrection`: registro administrativo de correcao futura.
- `CharacterHitPointComponent`: componente auditavel de PV por nivel.
- `CombatStyleLevel`, `CombatStyleLevelFeature`, `LevelChoiceGroup`, `CombatStyleTechniqueOption`: catalogo versionado.
- `BasicAbility`, `CharacterBasicAbility`: catalogo e concessao de Habilidade Basica.

## Services

O modulo `characters.level_up_service` centraliza autorizacao, cancelamento, inicio, rascunho, preview, validacoes e conclusao transacional.

A conclusao usa `transaction.atomic()` e bloqueia autorizacao/personagem/processo com `select_for_update()`.

## Ambiguidades e decisoes

- O livro permite rolagem ou metodo fixo para PV nos niveis seguintes; esta entrega fixa o metodo medio arredondado para cima, por requisito de produto.
- A criacao atual do sistema calcula PP inicial por regra antiga (`nivel + modificador de Vontade`). A passagem de nivel usa `level * 2` e documenta a divergencia sem alterar o fluxo de criacao.
- Personagens antigos podem nao possuir `CharacterHitPointComponent`; nesses casos o maximo de PV e recomposto pelo dado do Estilo, nivel resultante e Constituicao atual.
- As tecnicas de 3o nivel foram cadastradas como opcoes predefinidas do livro. Criacao personalizada de tecnicas depende de aprovacao do mestre e nao foi automatizada nesta entrega.
