# Criação de Personagens - OP RPG Livro do Jogador 1.5.7

Fonte exclusiva: `OP RPG - Livro do Jogador 1.5.7.pdf`.
Versão cadastrada: `player-book-1.5.7`.

Este documento registra somente as regras necessárias para a implementação do assistente.

## Ordem de Criação

| Páginas | Regra | Interpretação técnica | Responsável | Testes |
| --- | --- | --- | --- | --- |
| 8-12 | A criação passa por espécie, estilo, profissão, atributos, descrição, equipamento e derivados. | O fluxo da aplicação usa etapas operacionais: conceito, espécie, estilo, profissão, atributos, antecedente, personalidade, pendências, equipamentos e revisão. | `CharacterCreation`, `PlayerCharacterCreateView` | `test_player_can_create_character_for_selected_campaign` |
| 11 | A descrição do personagem inclui dados narrativos como altura e peso, além de antecedente, sonho e caminho. | A etapa Conceito armazena idade, altura, peso e caminho no rascunho; a confirmação copia esses campos para a ficha final. | `CharacterCreationConceptForm`, `confirm_creation`, `Character` | `test_creation_wizard_renders_pt_br_labels`, `test_confirmation_creates_character_with_breakdowns_and_origins` |
| 136-137 | Caminho é a combinação entre realização desejada e forma de trilhar o sonho, gerando nove caminhos. | `dream_path` usa enum fechado com os nove caminhos do livro e é exibido como "Caminho" na ficha. | `DREAM_PATH_CHOICES`, `PlayerCharacterSheetForm` | `test_character_sheet_uses_final_visual_layout_with_character_data`, `test_player_can_update_subjective_sheet_fields` |

## Atributos

| Páginas | Regra | Interpretação técnica | Responsável | Testes |
| --- | --- | --- | --- | --- |
| 9-10, 14 | Usar Força, Destreza, Constituição, Sabedoria, Vontade e Presença. | `Character` mantém campos legados, mas o assistente grava os seis atributos canônicos e o detalhamento em `CharacterAttribute`. | `CANONICAL_ATTRIBUTES`, `CharacterAttribute` | `test_seed_catalog_is_idempotent_and_complete` |
| 9-10 | Conjunto padrão 15, 14, 13, 12, 10, 8. | O assistente usa distribuição por pontos equivalente: 72 pontos totais, mínimo 8 e máximo 15 antes dos bônus. O conjunto padrão continua validável como caso compatível. | `point_distribution_is_valid`, `standard_array_is_valid` | `test_calculation_services` |
| 9-10 | Aleatório: 4d6, descarta o menor, seis vezes. | Serviço puro gera valores e guarda rolagens. | `generate_random_attribute_values` | `test_calculation_services` |
| 9-10 | Modificador `(atributo - 10) // 2`. | Função pura centralizada. | `calculate_attribute_modifier` | `test_calculation_services` |
| 14 | Limite inicial 20. | Validação falha se bônus elevam atributo acima de 20. Bônus raciais são escolhidos na etapa de espécie; bônus de antecedente na etapa de antecedente; a etapa de atributos exibe esses bônus automaticamente e só edita valores base. | `validate_creation`, forms de criação | `test_validation_rejects_invalid_dependencies`, `test_species_and_background_forms_store_attribute_bonuses_before_attribute_step` |

## Espécies e Variantes

| Páginas | Regra | Interpretação técnica | Responsável | Testes |
| --- | --- | --- | --- | --- |
| 13-30 | Espécies: Anão, Celestial, Gigante, Humano, Lunariano, Mestiço, Mink, Povo do Mar. | Catálogo versionado com PV base, tamanho, deslocamento, nado, preconceito, benefícios, dificuldades e escolhas obrigatórias. | `Species`, seed `seed_player_book_rules_1_5_7` | `test_each_species_and_variant_is_available` |
| 17-18, 21-23, 27-30 | Celestial, Humano, Mink e Povo do Mar exigem variantes. | A variante é FK e a validação confere se pertence à espécie. | `SpeciesVariant`, `validate_creation` | `test_validation_rejects_invalid_dependencies` |
| 26-27 | Mestiço deriva PV pela média das origens, deslocamento/nado pelo maior e exige duas origens. | `Mestiço` não é tratado como espécie estática na criação; usa `mixed_species_origins`. | `derive_mixed_species_values`, `CharacterCreation.mixed_species_origins` | `test_mixed_species_values`, `test_complete_mixed_species_requires_two_origins` |
| 27-30 e Cap. 6 | Minks e Povo do Mar podem usar traços Zoan para ancestralidade. | Foram cadastradas referências reutilizáveis a traços comuns/específicos/predador; aprovação do mestre controla coerência. | `ZoanAncestryTrait`, `validate_creation` | `test_complete_creation_examples` |

## Estilos de Combate

| Páginas | Regra | Interpretação técnica | Responsável | Testes |
| --- | --- | --- | --- | --- |
| 31-104 | Dez estilos oficiais com dado de vida, salvaguardas, perícias, proficiências, atributo primário, arma favorita, habilidade inata, equipamento e dinheiro inicial. | Dados estruturados em catálogo, não só texto descritivo. | `CombatStyle`, `rules_data.COMBAT_STYLES` | `test_seed_catalog_is_idempotent_and_complete`, `test_complete_creation_examples` |
| 31-104 | Perícias do estilo têm lista e quantidade próprias. | Form e validação usam `allowed_skills`, `skill_choice_count` e removem escolhas incompatíveis. | `CharacterCreationStyleForm`, `validate_creation` | `test_validation_rejects_invalid_dependencies` |

## Profissões

| Páginas | Regra | Interpretação técnica | Responsável | Testes |
| --- | --- | --- | --- | --- |
| 105-134 | Profissões principais: Adestrador, Arqueólogo, Caçador de Recompensas, Carpinteiro, Combatente, Cozinheiro, Engenheiro, Médico, Músico e Navegador. | `Profession` guarda perícias, Perícia Especial, ferramentas, itens e conhecimentos. | `Profession`, seed | `test_seed_catalog_is_idempotent_and_complete` |
| 133-134 | Timoneiro é subprofissão de Navegador. | `Profession.parent` aponta para Navegador; validação bloqueia sem Navegador. | `Profession`, `validate_creation` | `test_timoneiro_requires_navegador` |
| 106-107 | Sem Profissão dá quatro características e bloqueia profissão posterior salvo mestre. | `Profession.is_no_profession` e `restrictions` guardam regra; validação bloqueia subprofissão e Haki/Sobrenatural/Sorte. | `Profession`, `validate_creation` | `test_no_profession_blocks_subprofession_and_forbidden_skills` |

## Antecedentes

| Páginas | Regra | Interpretação técnica | Responsável | Testes |
| --- | --- | --- | --- | --- |
| 144-147 | Doze antecedentes oficiais, cada um com duas perícias, atributo recomendado e característica especial. | Catálogo `Background` com `allowed_skills`, `recommended_attribute` e `special_feature_name`. | `Background`, seed | `test_seed_catalog_is_idempotent_and_complete` |
| 145 | Nobre: História, Intuição, Investigação, Natureza e Sorte; recomendado Sabedoria. | Conferido no bloco do PDF porque o resumo inicial marcava como pendente. | `rules_data.BACKGROUNDS` | `test_complete_creation_examples` |
| 144 | Antecedente pode ser personalizado com Narrador. | Jogador não edita livremente; exceção fica registrada por mestre. | `CharacterRuleException` | `test_master_exception_allows_completion_and_is_recorded` |

## Proficiências e Derivados

| Páginas | Regra | Interpretação técnica | Responsável | Testes |
| --- | --- | --- | --- | --- |
| 226-234, 290-292 | Perícias mapeadas por atributo; Constituição não tem perícias gerais. | Seed atualiza `Skill` para os atributos canônicos. | `Skill`, `RuleProficiency` | `test_seed_catalog_is_idempotent_and_complete` |
| 226-234 | Proficiência repetida não soma duas vezes. | Sobreposição entre estilo, profissão e antecedente não bloqueia a criação. `CharacterProficiency` preserva cada origem; `CharacterSkill` mantém uma única proficiência efetiva para cálculo. | `CharacterProficiency`, `proficiency_resolution_service`, `character_creation_service` | `test_confirmation_creates_character_with_breakdowns_and_origins`, `test_overlapping_skill_choices_do_not_block_confirmation_or_stack_bonus` |
| 10-11, 31-104 | PV inicial: dado máximo do estilo + modificador de Constituição + PV base da espécie. | Cálculo centralizado e usado na confirmação. | `calculate_initial_hp`, `preview_derived_values` | `test_calculation_services`, `test_confirmation_creates_character_with_breakdowns_and_origins` |
| 10-11 | CR padrão 10 + Destreza; iniciativa Destreza; carga Força x 10. | Funções puras usadas na prévia e confirmação. | `character_calculation_service` | `test_calculation_services` |

## Ambiguidades e Decisões

| Regra | Ambiguidade | Decisão técnica |
| --- | --- | --- |
| Origem | O livro usa antecedentes como tipo de origem, mas não há um sistema separado chamado "origem" no trecho normativo da criação. | Não foi criado um segundo eixo de origem. O sistema mantém `Background` como Antecedente e adiciona `Caminho`, que estava faltando no Passo V. |
| Pontos de Treinamento racial por Sabedoria em Anões/Celestiais | O texto combina mínimo 1 com indisponibilidade quando o modificador é negativo. | Serviço retorna `0` para modificador não positivo e documenta que a liberação depende de recalcular quando Sabedoria ficar positiva. |
| Distribuição por pontos | O PDF apresenta conjunto padrão/rolagem; o ajuste de produto exige distribuição por pontos. | Usar soma do conjunto padrão como total (`72`) e seus extremos como mínimo/máximo base (`8` a `15`) preserva a escala do livro sem introduzir valores fora da fonte. |
| Coerência de traços Zoan | O livro exige coerência e aprovação do Narrador, mas isso é julgamento narrativo. | Traços específicos/predador exigem aprovação do mestre ou marcação explícita de ancestral carnívoro caçador. |
| Requisitos raciais de estilos específicos | Algumas restrições dependem de interpretação do texto completo. | Requisitos ficam em JSON estruturado e podem ser ignorados via `CharacterRuleException` registrada pelo mestre. |
| Equipamento de Gigante | O livro exige adaptação de equipamento ao tamanho. | O catálogo registra a necessidade; a entrega inicial cria itens textuais e deixa compatibilidade detalhada para resolução de equipamento posterior, sem progressão pós-1º nível. |
