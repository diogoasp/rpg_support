# Plano de Implementação — Sistema de Apoio à Campanha One Piece RPG

## 1. Objetivo do projeto

Desenvolver uma aplicação web em Django para apoiar uma campanha presencial de RPG baseada no universo de One Piece.

O sistema não deve funcionar como mesa virtual. Sua função é:

* centralizar fichas e inventários;
* disponibilizar mapas, imagens e registros das sessões;
* auxiliar o mestre na preparação e condução de combates;
* permitir reprodução rápida de músicas, falas e efeitos sonoros;
* reduzir controles manuais;
* evitar que o mestre passe tempo excessivo interagindo com a aplicação durante a sessão.

A experiência deve priorizar poucos cliques, carregamentos mínimos e interfaces compactas.

---

# 2. Stack técnica

## Backend

* Python 3.12+
* Django 5.x
* Django REST Framework apenas quando necessário
* PostgreSQL
* Pillow
* django-environ
* Gunicorn

## Frontend

* Django Templates
* Bootstrap 5
* HTMX
* Alpine.js apenas para comportamentos locais simples
* Bootstrap Icons

Não implementar SPA.

## Infraestrutura

* VPS Ubuntu
* Nginx
* Gunicorn
* PostgreSQL
* arquivos estáticos servidos pelo Nginx
* arquivos de mídia armazenados inicialmente no servidor
* suporte futuro a S3 ou Cloudflare R2

---

# 3. Princípios obrigatórios de UX

1. A aplicação não é uma mesa virtual.
2. Jogadores não precisam permanecer conectados durante a sessão.
3. A tela principal do mestre deve concentrar as ações mais usadas.
4. Ações recorrentes devem exigir no máximo um ou dois cliques.
5. Durante o combate, evitar recarregamentos completos de página.
6. Usar HTMX para:

   * aplicar dano;
   * curar;
   * atualizar PV;
   * alterar recursos do navio;
   * adicionar itens;
   * reproduzir ou selecionar áudio;
   * alterar condições.
7. Não criar formulários excessivamente detalhados.
8. Campos avançados devem ser opcionais.
9. O mestre sempre deve poder sobrescrever resultados automáticos.
10. O sistema deve funcionar adequadamente em notebook e desktop.

---

# 4. Estrutura inicial do projeto

Criar o projeto com a seguinte estrutura:

```text
config/
accounts/
campaigns/
characters/
inventory/
ships/
maps/
history/
enemies/
encounters/
combat/
audio_panel/
dashboard/
templates/
static/
media/
```

---

# 5. Módulo de autenticação e usuários

## 5.1. Modelo de usuário

Usar `AbstractUser`.

Campos adicionais:

```python
role = models.CharField(
    max_length=20,
    choices=[
        ("master", "Mestre"),
        ("player", "Jogador"),
    ],
)
```

## 5.2. Regras

### Mestre

Pode:

* criar e editar campanhas;
* criar e editar personagens;
* visualizar todas as fichas;
* editar inventários;
* gerenciar navios;
* gerenciar mapas;
* publicar registros de sessões;
* cadastrar inimigos;
* gerar encontros;
* conduzir combates;
* controlar áudios.

### Jogador

Pode:

* visualizar apenas sua ficha;
* visualizar apenas seu inventário;
* visualizar o navio da campanha;
* visualizar mapas liberados;
* visualizar registros publicados da história;
* visualizar o dashboard de jogador.

Não pode:

* acessar ficha de outro jogador;
* editar PV, PP ou atributos;
* acessar ferramentas do mestre;
* visualizar inimigos;
* visualizar encontros;
* visualizar mapas privados.

## 5.3. Implementação de permissões

Criar mixins:

```python
MasterRequiredMixin
PlayerRequiredMixin
CampaignMemberRequiredMixin
CharacterOwnerRequiredMixin
```

Não depender apenas de ocultação de botões no frontend.

Validar permissões também no backend.

---

# 6. Módulo de campanhas

## Modelo `Campaign`

Campos:

```python
name
slug
description
cover_image
master
players
is_active
created_at
updated_at
```

Regras:

* cada campanha possui um mestre;
* uma campanha pode possuir vários jogadores;
* inicialmente, cada jogador terá apenas um personagem por campanha;
* manter arquitetura preparada para múltiplas campanhas.

---

# 7. Módulo de personagens

## 7.1. Modelo principal

Criar `Character`.

Campos:

```python
campaign
user
name
portrait
level
species
profession
combat_style
background
bounty

armor_class
proficiency_bonus
initiative
movement

max_hp
current_hp
max_power_points
current_power_points

strength
dexterity
constitution
intelligence
wisdom
charisma

haki_declared
haki_trained
devil_fruit_name
devil_fruit_available

notes
created_at
updated_at
```

## 7.2. Regras da campanha

* nenhum personagem começa com Akuma no Mi;
* `devil_fruit_available` deve iniciar como `False`;
* personagens podem ter Haki declarado;
* Haki declarado não significa Haki utilizável;
* `haki_trained` deve iniciar como `False`;
* o uso intencional de Haki depende de treinamento concedido pelo mestre.

## 7.3. Modelos auxiliares

Criar:

```python
Skill
CharacterSkill
CharacterTechnique
CharacterFeature
CharacterCondition
```

### `CharacterTechnique`

Campos mínimos:

```python
character
name
description
action_type
range
damage
cost
is_available
sort_order
```

### `CharacterCondition`

Campos:

```python
character
name
description
is_active
```

## 7.4. Interface

A ficha deve ter:

* modo completo;
* modo compacto;
* modo impressão.

A ficha compacta deve mostrar:

* nome;
* retrato;
* nível;
* PV;
* PP;
* CR;
* iniciativa;
* condições;
* técnicas principais.

---

# 8. Módulo de inventário

## 8.1. Modelo `InventoryItem`

Campos:

```python
character
name
description
image
file
quantity
master_note
is_visible
created_at
updated_at
```

Regras:

* `quantity` deve ser opcional;
* um item pode ser apenas texto;
* um item pode ser imagem;
* um item pode ser arquivo;
* mapas, cartas e documentos podem existir como itens;
* o mestre pode adicionar ou remover itens;
* o jogador apenas visualiza.

## 8.2. Ações rápidas

No dashboard do mestre:

```text
Selecionar jogador
Adicionar item
Preencher nome
Anexar imagem ou arquivo opcional
Salvar
```

Implementar em modal com HTMX.

## 8.3. Exclusão

Preferir exclusão lógica:

```python
is_active = models.BooleanField(default=True)
```

---

# 9. Módulo de navio

## 9.1. Modelo `Ship`

Campos:

```python
campaign
name
image
category
description

max_hp
current_hp

resistance_class
resistance_bonus
speed

max_crew
current_crew

navigation_resources
condition

cannons
facilities
notes
updated_at
```

## 9.2. Recursos de navegação

Usar escolhas simples:

```python
RESOURCE_LEVELS = [
    ("abundant", "Abundantes"),
    ("adequate", "Adequados"),
    ("low", "Baixos"),
    ("critical", "Críticos"),
    ("empty", "Esgotados"),
]
```

## 9.3. Condição automática

Calcular a condição do navio com base no percentual de PV.

Criar propriedade:

```python
@property
def hp_percentage(self):
    ...
```

Criar propriedade:

```python
@property
def calculated_condition(self):
    ...
```

A condição deve ser derivada sempre que possível.

## 9.4. Gestão rápida

No dashboard do mestre, mostrar:

```text
Nome do navio
PV atual / PV máximo
Condição
Recursos
Botão: causar dano
Botão: reparar
```

Aplicar dano e reparo via modal HTMX.

## 9.5. Permissões

* todos os jogadores da campanha podem visualizar;
* apenas o mestre pode editar.

---

# 10. Módulo de mapas

## Modelo `CampaignMap`

Campos:

```python
campaign
title
description
image
file
is_visible_to_players
visible_to_specific_players
is_inventory_item
created_at
updated_at
```

Tipos sugeridos:

```python
WORLD
ISLAND
LOCAL
SHIP
TREASURE
DOCUMENT
OTHER
```

Regras:

* mapas privados aparecem apenas para o mestre;
* o mestre pode liberar um mapa durante a sessão;
* a liberação deve ser feita por um botão simples;
* jogadores só visualizam mapas liberados.

---

# 11. Módulo de história

## 11.1. Modelo `SessionRecord`

Campos:

```python
campaign
session_number
title
session_date
cover_image
summary
audio_file
transcription
is_published
created_at
updated_at
```

## 11.2. Objetivo

A história deve ser uma área de consulta, não um gerenciador detalhado de plots.

Não criar inicialmente:

* árvore de decisões;
* gestão de cenas;
* relacionamentos narrativos complexos;
* estados automáticos de plots.

## 11.3. Fluxo

1. Mestre cria o registro da sessão.
2. Adiciona resumo.
3. Opcionalmente anexa áudio.
4. Opcionalmente cola transcrição.
5. Publica.
6. Jogadores visualizam registros publicados em ordem cronológica.

## 11.4. Preparação para IA

Adicionar campos opcionais:

```python
ai_summary
ai_decisions
ai_detected_items
ai_processed_at
```

Não implementar integração com IA no primeiro MVP.

Criar apenas a estrutura preparada para integração futura.

---

# 12. Catálogo de inimigos

## 12.1. Modelo `Enemy`

Campos:

```python
name
image
description

category
faction
difficulty_tier
challenge_rating
recommended_level

max_hp
armor_class
resistance_bonus
initiative
movement

strength
dexterity
constitution
intelligence
wisdom
charisma

is_boss
is_named_character
is_canon_character
operational_complexity
is_available_for_generator
notes
```

## 12.2. Complexidade operacional

Escolhas:

```python
SIMPLE
MODERATE
COMPLEX
```

O gerador deve priorizar inimigos simples para grupos iniciantes.

## 12.3. Personagens muito poderosos

Criar campo:

```python
encounter_mode = models.CharField(
    choices=[
        ("normal", "Confronto normal"),
        ("reduced", "Versão reduzida"),
        ("narrative", "Encontro narrativo"),
        ("not_recommended", "Não recomendado"),
    ]
)
```

Almirantes, Shichibukai e personagens equivalentes não devem ser sugeridos automaticamente em encontros normais.

## 12.4. Ataques e técnicas

Criar:

```python
EnemyAction
```

Campos:

```python
enemy
name
description
action_type
attack_bonus
damage
range
resource_cost
sort_order
```

---

# 13. Gerador de encontros

## 13.1. Entradas

O formulário deve solicitar apenas:

```text
Jogadores participantes
Dificuldade
Quantidade aproximada de inimigos
Com chefe ou sem chefe
Facção opcional
Ambiente opcional
Inimigo obrigatório opcional
```

## 13.2. Dificuldades

```python
EASY
MEDIUM
HARD
```

## 13.3. Cálculo inicial

Calcular:

```python
party_size
average_level
total_party_level
average_hp
```

Criar um algoritmo inicial simples, configurável e legível.

Não usar lógica excessivamente complexa no primeiro MVP.

## 13.4. Estratégia do gerador

### Fácil

* poucos inimigos;
* inimigos simples;
* baixo dano explosivo;
* ausência de chefe ou chefe fraco;
* margem alta para erros dos jogadores.

### Médio

* quantidade equilibrada;
* um inimigo mais resistente ou líder;
* algumas habilidades especiais.

### Difícil

* maior pressão;
* inimigos com funções diferentes;
* chefe opcional;
* risco real sem pressupor morte inevitável.

## 13.5. Inimigo obrigatório

Caso o mestre selecione um inimigo específico:

* incluí-lo na composição;
* recalcular os demais inimigos;
* exibir alerta quando o inimigo for inadequado;
* permitir continuar mesmo com alerta.

## 13.6. Resultado

Exibir:

```text
Composição sugerida
Estimativa de dificuldade
Alertas
Inimigos selecionados
PV total estimado
Quantidade de ações inimigas
Complexidade operacional
```

Ações:

```text
Aceitar encontro
Substituir inimigo
Adicionar inimigo
Remover inimigo
Editar PV
Salvar
Iniciar combate
```

---

# 14. Módulo de encontros

## Modelo `Encounter`

Campos:

```python
campaign
name
difficulty
status
has_boss
environment
faction
notes
created_by
created_at
started_at
finished_at
```

## Modelo `EncounterParticipant`

Campos:

```python
encounter
character
```

## Modelo `EncounterEnemy`

Campos:

```python
encounter
enemy
display_name
max_hp_override
quantity
```

---

# 15. Módulo de combate

## 15.1. Modelo `Combat`

Campos:

```python
encounter
campaign
status
round_number
current_turn_index
started_at
finished_at
```

## 15.2. Modelo `Combatant`

Campos:

```python
combat
character
enemy
display_name
combatant_type

max_hp
current_hp

max_power_points
current_power_points

armor_class
resistance_bonus
initiative
turn_order

is_defeated
is_active
```

Criar uma instância separada para cada inimigo.

Exemplo:

```text
Marinheiro 1
Marinheiro 2
Marinheiro 3
```

## 15.3. Modelo `CombatCondition`

Campos:

```python
combatant
name
description
duration_rounds
expires_at_round
is_active
```

## 15.4. Modelo `CombatEvent`

Usar apenas para auditoria e desfazer ações.

Campos:

```python
combat
round_number
actor
target
event_type
raw_value
final_value
description
created_at
is_reverted
```

Não transformar o log técnico em narrativa oficial.

---

# 16. Painel de combate

## 16.1. Layout

Exibir:

* rodada atual;
* combatente atual;
* ordem de iniciativa;
* jogadores;
* inimigos;
* PV;
* PP;
* CR;
* condições;
* ações rápidas.

## 16.2. Ações rápidas

Para cada combatente:

```text
Dano
Cura
Condição
Remover condição
Derrotar
Detalhes
```

## 16.3. Aplicação de dano

Fluxo:

1. mestre informa dano bruto;
2. sistema sugere redução;
3. sistema calcula dano final;
4. mestre confirma ou sobrescreve;
5. interface atualiza apenas o combatente afetado.

Exemplo:

```text
Dano bruto: 14
Redução: 4
Dano final: 10
PV: 35 → 25
```

## 16.4. Desfazer

Guardar o último evento aplicado.

Disponibilizar botão:

```text
Desfazer última alteração
```

## 16.5. Navegação de turnos

Botões:

```text
Turno anterior
Próximo turno
Próxima rodada
Encerrar combate
```

Ao avançar turno:

* atualizar combatente atual;
* verificar condições expiradas;
* exibir aviso;
* não remover automaticamente sem confirmação quando houver ambiguidade.

---

# 17. Painel de áudio

## 17.1. Modelo `AudioAsset`

Campos:

```python
campaign
title
audio_file
category
character_name
scene_name
is_favorite
volume_default
loop_default
sort_order
created_at
```

Categorias:

```python
MUSIC
AMBIENCE
NPC_VOICE
SOUND_EFFECT
OPENING
ENDING
OTHER
```

## 17.2. Interface

Criar painel persistente no dashboard do mestre.

Controles:

```text
Tocar
Pausar
Parar
Volume
Loop
Fade-out
Parar todos
```

## 17.3. Requisitos técnicos

A reprodução deve ocorrer no navegador do mestre.

Usar API de áudio do navegador.

Não transmitir áudio para dispositivos dos jogadores.

## 17.4. Acesso rápido

Exibir:

* favoritos;
* últimos utilizados;
* categorias;
* busca textual.

Evitar recarregar página ao iniciar áudio.

---

# 18. Dashboard do jogador

Criar uma única tela principal.

## Blocos

### Personagem

* retrato;
* nome;
* nível;
* PV;
* PP;
* CR;
* iniciativa;
* condições.

### Técnicas

* técnicas favoritas ou principais;
* acesso à ficha completa.

### Inventário

* itens mais recentes;
* quantidade total;
* itens ainda não visualizados.

### Navio

* imagem;
* nome;
* PV;
* condição;
* recursos.

### História

* última sessão publicada;
* acesso ao histórico.

### Mapas

* últimos mapas liberados.

---

# 19. Dashboard do mestre

A tela principal do mestre deve ser otimizada para uso durante a sessão.

## 19.1. Cabeçalho fixo

Exibir:

```text
Campanha atual
Navio
PV do navio
Sessão atual
Combate ativo
```

## 19.2. Ações rápidas

```text
Gerar encontro
Continuar combate
Adicionar item
Dano ao navio
Reparar navio
Abrir mapa
Liberar mapa
Abrir painel de áudio
```

## 19.3. Jogadores

Exibir cards compactos:

```text
Retrato
Nome
PV
PP
CR
Condições
Inventário rápido
```

## 19.4. Combate ativo

Caso exista combate ativo, ele deve ocupar a área principal.

Caso não exista, mostrar:

* personagens;
* navio;
* encontros recentes;
* áudios favoritos;
* mapas recentes.

## 19.5. Minimização de carregamentos

Usar HTMX para:

* modais;
* cards;
* atualizações parciais;
* formulários rápidos;
* feedback visual.

---

# 20. API interna

Usar endpoints JSON apenas quando necessário.

Possíveis endpoints:

```text
/api/characters/<id>/summary/
/api/ships/<id>/status/
/api/encounters/generate/
/api/combat/<id>/state/
/api/audio-assets/
```

Preferir views Django com HTMX para ações simples.

Não criar API completa antecipadamente.

---

# 21. Testes

## 21.1. Testes obrigatórios de permissão

* jogador não acessa personagem de outro jogador;
* jogador não edita inventário;
* jogador não acessa combate;
* jogador não acessa inimigos;
* jogador não acessa mapas privados;
* mestre acessa recursos da própria campanha;
* usuário de outra campanha não acessa dados indevidos.

## 21.2. Testes de domínio

* PV nunca ultrapassa máximo;
* PV não fica abaixo de zero;
* PP nunca ultrapassa máximo;
* condição do navio é calculada corretamente;
* dano é aplicado corretamente;
* resistência pode ser sobrescrita;
* encontro respeita inimigo obrigatório;
* inimigos narrativos geram alerta;
* Akuma no Mi inicia indisponível;
* Haki treinado inicia indisponível.

## 21.3. Testes de interface

Usar testes funcionais apenas nos fluxos críticos:

* login;
* dashboard do mestre;
* adicionar item;
* gerar encontro;
* iniciar combate;
* aplicar dano;
* reproduzir áudio;
* liberar mapa.

---

# 22. Auditoria

Criar modelo simples:

```python
ActivityLog
```

Campos:

```python
campaign
user
action
object_type
object_id
description
created_at
```

Registrar apenas ações críticas:

* alteração de PV;
* alteração do navio;
* adição ou remoção de item;
* liberação de mapa;
* início e fim de combate;
* publicação de sessão.

Não registrar cada visualização.

---

# 23. Seed inicial

Criar comando:

```bash
python manage.py seed_rpg
```

O comando deve criar:

* usuário mestre;
* dois jogadores;
* campanha de teste;
* personagens;
* navio;
* itens;
* mapas;
* áudios fictícios;
* inimigos simples;
* um chefe;
* um encontro de teste.

Não incluir material protegido por direitos autorais diretamente no repositório.

Usar dados fictícios ou placeholders.

---

# 24. Administração Django

Registrar todos os modelos relevantes no Django Admin.

Configurar:

* filtros;
* busca;
* autocomplete;
* listagem compacta;
* edição inline quando pertinente.

O admin pode ser usado inicialmente para cadastros menos frequentes, como:

* catálogo de inimigos;
* técnicas;
* áudios;
* mapas;
* registros históricos.

---

# 25. Segurança

Implementar:

* CSRF;
* validação de upload;
* limite de tamanho para arquivos;
* validação de MIME type;
* nomes de arquivos seguros;
* proteção de arquivos privados;
* autorização antes de servir mapas e documentos;
* configuração segura de cookies;
* `DEBUG=False` em produção;
* variáveis sensíveis em `.env`.

Arquivos privados não devem ser acessíveis apenas por URL pública previsível.

Criar view protegida para download quando necessário.

---

# 26. Performance

Aplicar:

* `select_related`;
* `prefetch_related`;
* índices em FKs;
* índices em campanha, usuário e status;
* paginação de história e mapas;
* thumbnails para imagens;
* lazy loading;
* cache opcional para dashboards.

Evitar consultas repetidas no dashboard do mestre.

Criar testes de contagem de queries nas páginas mais acessadas.

---

# 27. Fases de implementação

## Fase 1 — Fundação

Implementar:

* projeto Django;
* configurações;
* usuário customizado;
* autenticação;
* roles;
* campanhas;
* permissões;
* layout base;
* navegação.

Critérios de aceite:

* mestre e jogador autenticam;
* cada role recebe dashboard correto;
* permissões são validadas no backend.

## Fase 2 — Personagens e inventário

Implementar:

* ficha;
* atributos;
* técnicas;
* condições;
* inventário;
* visualização compacta;
* impressão.

Critérios de aceite:

* jogador vê apenas sua ficha;
* mestre edita ficha;
* mestre adiciona item via modal;
* jogador visualiza item imediatamente.

## Fase 3 — Navio, mapas e história

Implementar:

* navio;
* cálculo de condição;
* recursos;
* mapas;
* visibilidade;
* registros de sessão;
* publicação.

Critérios de aceite:

* todos os jogadores veem o navio;
* somente mestre edita;
* mapas privados não aparecem;
* sessões não publicadas não aparecem.

## Fase 4 — Inimigos e encontros

Implementar:

* catálogo;
* ações;
* inimigos nomeados;
* gerador;
* salvamento de encontro.

Critérios de aceite:

* encontro pode ser gerado por participantes;
* dificuldade é exibida;
* mestre pode editar composição;
* inimigos inadequados geram alerta.

## Fase 5 — Combate

Implementar:

* início do combate;
* combatentes;
* iniciativa;
* rodada;
* dano;
* cura;
* condições;
* desfazer;
* encerramento.

Critérios de aceite:

* atualização sem reload completo;
* dano aplicado corretamente;
* cada inimigo mantém PV separado;
* combate pode ser retomado.

## Fase 6 — Áudios e dashboard operacional

Implementar:

* biblioteca de áudio;
* player;
* favoritos;
* painel persistente;
* integração com dashboard do mestre.

Critérios de aceite:

* áudio inicia sem reload;
* áudio pode ser pausado;
* volume pode ser alterado;
* todos os áudios podem ser interrompidos;
* painel permanece acessível durante combate.

## Fase 7 — Polimento e produção

Implementar:

* testes;
* otimização;
* logs;
* proteção de arquivos;
* backup;
* deploy;
* documentação.

---

# 28. Backlog futuro

Não implementar no MVP:

* transcrição automática;
* resumo por IA;
* geração automática de histórias;
* rolagem online;
* mapa tático;
* grid;
* chat;
* movimento de tokens;
* videoconferência;
* marketplace;
* aplicativo mobile;
* notificações push;
* integração com WhatsApp;
* controle detalhado de comida;
* controle detalhado de viagens;
* editor complexo de regras.

Possíveis versões futuras:

* transcrição de sessões;
* geração assistida de resumo;
* identificação automática de decisões;
* sugestão de itens recebidos;
* integração com modelos de IA;
* exportação de ficha em PDF;
* importação estruturada de inimigos;
* geração de cartazes de procurado.

---

# 29. Ordem de execução para o Codex

O Codex deve trabalhar em pequenas entregas.

Para cada etapa:

1. analisar os modelos existentes;
2. criar ou atualizar testes;
3. implementar models;
4. criar migrations;
5. implementar services;
6. implementar views;
7. implementar templates;
8. implementar HTMX;
9. executar testes;
10. documentar mudanças.

Não implementar várias fases simultaneamente.

Cada entrega deve:

* manter o projeto executável;
* não quebrar testes anteriores;
* incluir migrations;
* incluir testes;
* informar arquivos alterados;
* informar decisões arquiteturais;
* informar pendências.
