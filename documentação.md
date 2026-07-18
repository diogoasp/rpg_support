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

---

# 30. Estado implementado — Fase 3 (2026-07-17)

## 30.1. Resumo e aplicações

Foram criadas as aplicações Django `ships`, `maps` e `history`, preservando templates Django, Bootstrap 5, HTMX e regras de domínio em services. A Fase 3 não introduz combate, inimigos, encontros, player operacional de áudio ou automação/IA.

## 30.2. Modelos e migrations

* `Ship` mantém histórico de navios por campanha e uma restrição parcial garante somente um ativo. Contém identificação, imagem, categoria, descrição, PV, CR/bônus, velocidade, tripulação simples, nível abstrato de recursos, canhões, instalações e observações. A migration é `ships/0001_initial.py`.
* `CampaignMap` contém tipo, imagem/PDF opcionais, destaque, ativação lógica, visibilidade global/específica e vínculo opcional a item de inventário. A migration é `maps/0001_initial.py`.
* `SessionRecord` contém número único por campanha, data, capa, resumo, áudio, transcrição, estado e instante de publicação. Campos futuros de IA são somente armazenamento opcional, sem processamento. A migration é `history/0001_initial.py`.
* FKs já produzem seus índices implícitos; foram adicionados apenas índices compostos dos filtros operacionais.

## 30.3. Services e decisões de domínio

Os services transacionais implementam criação/substituição do navio ativo, dano, reparo, recursos e tripulação; criação, visibilidade e desativação de mapas; criação, publicação e despublicação de sessões. Todos validam mestre e pertencimento à campanha no backend. Não havia `ActivityLog` no estado anterior, portanto não se criou auditoria isolada nesta fase para evitar antecipar/reformular arquitetura; essa pendência permanece explícita.

O percentual de PV é derivado. A condição usa limites centralizados: mais de 75% Normal; mais de 50% Avariado; mais de 25% Danificado; de 1% a 25% Muito danificado; zero Inoperante. Dano aceita bruto, redução sugerida e valor final opcional; nunca reduz abaixo de zero. Reparos nunca superam o máximo.

## 30.4. Permissões, visibilidade e arquivos

O mestre administra apenas campanhas próprias. Membros veem o navio ativo. Mapas ativos requerem a chave global; sem usuários selecionados são visíveis a todos os jogadores da campanha e, com seleção, somente aos selecionados. O mestre sempre vê mapas de suas campanhas. Rascunhos de sessão são privados; publicação preenche `published_at`; despublicação preserva esse instante como registro da última publicação.

Mapas/imagens, PDFs, capas e áudios são servidos por `FileResponse` após autenticação, associação à campanha e regra de visibilidade. Os IDs são resolvidos no banco, sem receber caminhos do cliente, impedindo traversal. Em produção, `MEDIA_ROOT` deve ficar fora de uma localização pública do Nginx; a evolução recomendada é trocar a resposta autorizada por `X-Accel-Redirect` para uma location `internal`. `PROTECTED_MEDIA_MODE` prepara essa configuração, mas o modo implementado nesta fase é `django`.

Uploads aceitos: JPEG/PNG/WebP até `MAX_IMAGE_UPLOAD_SIZE`, PDF até `MAX_DOCUMENT_UPLOAD_SIZE`, e MP3/M4A/OGG/WAV até `MAX_AUDIO_UPLOAD_SIZE`. Extensão/MIME são avaliados pelo upload; conteúdo não é convertido nem processado.

## 30.5. Rotas, formulários e templates

Rotas compartilhadas: `/navio/`, `/mapas/`, `/historia/`, detalhe de sessão e endpoints protegidos de mídia. Rotas do mestre são contextualizadas pelo slug em `/mestre/<slug>/navio/`, `/mestre/<slug>/mapas/` e `/mestre/<slug>/historia/`, reduzindo ambiguidades com múltiplas campanhas.

Há formulários separados para navio, dano, reparo, recursos, mapa, visibilidade, sessão e confirmação de publicação. Fragmentos HTMX atualizam somente card de navio, card de mapa ou badge de sessão. Cadastros extensos usam páginas completas. Templates de jogador não apresentam controles administrativos.

## 30.6. Dashboards, admin e seed

Os dashboards fazem prefetch do navio ativo, mapas autorizados/recentes e sessões relevantes, evitando queries em loops. O jogador recebe cards compactos; o mestre recebe ações operacionais de navio, mapas e histórico. Os três modelos foram registrados no admin com busca, filtros, relações antecipadas e datas somente leitura.

`seed_rpg` permanece idempotente e cria a campanha de desenvolvimento `Tambores da Libertação`, o navio `Caravela revolucionária de apoio`, três mapas (público, privado e específico) e três sessões (duas publicadas e um rascunho), sem arquivos protegidos por direitos autorais.

## 30.7. Divergências, limitações e pendências

* O arquivo histórico chamava-se `documentação.MD`, enquanto a solicitação referencia `documentação.md`; ele foi apenas renomeado, com todo o conteúdo anterior preservado.
* A documentação original sugeria um campo editável `condition`; a implementação segue o requisito mais seguro desta fase e mantém condição exclusivamente derivada.
* Não existia infraestrutura de thumbnails; imagens usam carregamento tardio e dimensões CSS, sem instalar biblioteca de PDF.
* Não existia exclusão lógica de sessões. Para evitar alterar o contrato com um campo não solicitado, sessões podem ser preservadas como rascunho; exclusão administrativa segue o padrão do Django Admin.
* Auditoria, X-Accel operacional, armazenamento externo e thumbnails permanecem melhorias futuras. IA, transcrição, combate, encontros, áudio operacional e plots permanecem para fases posteriores.

---

# 31. Estado implementado — Fase 4 (2026-07-17)

## 31.1. Resumo, aplicações e escopo

Foram criadas as aplicações `enemies` e `encounters`. A primeira mantém um catálogo global reutilizável, administrável somente por mestres; a segunda mantém encontros necessariamente vinculados à campanha. A opção global evita cópias do mesmo adversário entre campanhas e segue o catálogo previsto no plano, enquanto o isolamento de encontros impede acesso cruzado. Não foi implementada qualquer execução de combate.

## 31.2. Modelos, classificações e migrations

`EnemyFaction` permite facções próprias. `Enemy` reúne identidade, imagem privada de catálogo, categoria, facção, ambiente, faixa recomendada, estatísticas, atributos de 1 a 30, flags de chefe/nomeado/canônico, complexidade, modo, override de ameaça, disponibilidade, comportamento e notas privadas. Categorias são lacaio, comum, elite, chefe, criatura, veículo e especial; ambientes são qualquer, urbano, floresta, deserto, montanha, mar, navio, ilha, subterrâneo e especial; complexidades são simples, moderada e complexa; modos são normal, reduzido, narrativo e não recomendado. Inativos tornam-se indisponíveis para geração.

`EnemyAction` armazena tipo, bônus/DC, alcance, alvo, dano e efeito textuais, custo, recarga e limites, sem parser ou execução. `EnemyFeature` separa resistências, sentidos e orientações passivas das ações, melhorando o bloco de referência rápida. A edição usa dois inline formsets na mesma transação por ser o padrão mais estável e simples.

`Encounter` armazena campanha, dificuldade solicitada, status, estimativa, ameaça, carga, alertas, notas e metadados JSON. `EncounterParticipant` garante unicidade e pertencimento à campanha. `EncounterEnemy` representa grupos, com quantidade e overrides, sem instâncias de combatentes. As migrations são `enemies/0001_initial.py` e `encounters/0001_initial.py`.

## 31.3. Balanceamento centralizado

`settings.ENCOUNTER_BALANCE` centraliza multiplicadores de dificuldade (0,70/1,00/1,35), pesos de complexidade (1/2/4), economia de ações (1,00 para um; 1,10 para dois; 1,25 até cinco; 1,50 até doze), máximo automático 12, proporção de alerta 2:1 e carga operacional de alerta 12. São parâmetros próprios, não uma tabela de XP externa, e deverão ser calibrados após sessões reais.

A ameaça base soma `PV/5 + ND×4 + defesa×0,8 + ações ativas×1,5 + complexidade`, aplica 1,15 a elites e 1,30 a chefes; `threat_score_override` substitui a fórmula. O orçamento soma `níveis×6 + PV médio×tamanho×0,35 + CR médio×tamanho×0,2` e aplica o multiplicador da dificuldade. A ameaça da composição recebe o multiplicador de economia de ações. A estimativa é fácil abaixo de 80% do orçamento, média abaixo de 120% e difícil nos demais casos.

## 31.4. Gerador, filtros, relaxamento e alertas

Os services tipados expõem `build_party_snapshot`, `enemy_threat_score`, `calculate_encounter_budget`, `calculate_action_economy_multiplier`, `calculate_operational_load`, `estimate_encounter_difficulty`, `filter_enemy_candidates`, `generate_encounter`, `recalculate_encounter_proposal`, `save_generated_encounter` e `duplicate_encounter`. A proposta usa dataclasses, seed determinística opcional e não salva automaticamente.

A seleção exige ativos/disponíveis e exclui sempre modos narrativo e não recomendado. Considera nível, facção, ambiente e chefe; relaxa primeiro ambiente e depois facção, informando os critérios. Com chefe escolhe no máximo um chefe ou elite líder; sem chefe não sugere chefes. Um inimigo obrigatório sempre entra, inclusive se manualmente indisponível, narrativo ou não recomendado, e produz alertas em vez de bloquear o mestre. Alertas também cobrem faixa de nível, orçamento individual, relação inimigos/jogadores e carga operacional.

## 31.5. Rotas, templates, HTMX e dashboard

O catálogo usa `/mestre/inimigos/`, criar, detalhe, editar e desativar, com busca, filtros e paginação. Encontros usam `/mestre/<slug>/encontros/`, gerador, proposta, salvamento, detalhe, duplicação e cancelamento. Templates exibem o bloco completo do inimigo, notas privadas, formulário seccionado, listagem e detalhe de encontros. O fragmento `encounters/partials/proposal.html` permite remover, alterar quantidade, nome, PV e chefe e recalcula ameaça/dificuldade/carga sem reload completo; erros usam fragmento padronizado.

O dashboard do mestre oferece gerar encontro, abrir preparados, catálogo e cadastro, além dos rascunhos/preparados recentes com participantes, grupos e chefe. Consultas usam `select_related`/`prefetch_related`. Jogadores recebem 403 em todas as rotas da fase; objetos de encontro são sempre resolvidos dentro da campanha do mestre.

## 31.6. Admin, uploads, seed e testes

Todos os modelos foram registrados no admin com busca, filtros, inlines, relações antecipadas, readonly e paginação. Imagens aceitam JPEG, PNG e WebP, validam extensão, MIME e limite configurável, usam nome UUID e não têm rota pública para jogadores. `seed_rpg` agora cria duas facções fictícias, quatro simples, dois moderados, elite, chefe, narrativo, não recomendado, ações, características e três encontros idempotentes.

A suíte cobre o legado e os novos contratos de domínio, geração, recálculo, salvamento, duplicação, permissões e HTMX. A execução inicial revelou três fragilidades preexistentes: captura de `IntegrityError` dentro da transação implícita do `TestCase`, argumento `instance` indevido em `DamageShipForm` e expectativa de landing após login incompatível com o redirect normal. Foram aplicadas correções mínimas: validação antecipada das duas unicidades, construção correta do formulário e uma landing de uso único após autenticação; o comportamento público normal do dashboard permanece inalterado.

## 31.7. Divergências e limitações

O prompt cita override de “CR” em `EncounterEnemy`, mas lista `armor_class_override`; adotou-se este último e `resistance_bonus_override`, coerentes com os nomes existentes. “Personagem ativo” foi interpretado pelo usuário ativo, pois `Character` não possui `is_active`; alterar o contrato de personagens seria desnecessário. O ambiente é filtro leve e não bloqueia seleção manual. A proposta fica temporariamente na sessão do mestre, sem banco antes da confirmação.

Ficam para a Fase 5: iniciativa, combatentes individuais, rodadas, turnos, dano, cura, condições, recursos, execução de ações, dados, logs e início real do combate. Permanecem fora do escopo combate naval, áudio, IA e importação de PDFs.

---

# 32. Estado implementado — Fase 5 (2026-07-17)

## 32.1. Painel narrativo e escopo

Foi criada a aplicação `combat` como painel exclusivo do mestre para confrontos presenciais. O modo padrão é Livre e concentra cards individuais, PV, estado narrativo, CR, resistência, chefe, ações principais e ficha rápida. Não foram introduzidos mapa, grid, tokens, dados, seleção de alvos, execução de ataques, WebSockets, IA ou log narrativo obrigatório.

## 32.2. Persistência e domínio

`Combat` vincula encontro e campanha, preserva modo, status, rodada/posição opcionais, configuração opcional de recursos dos jogadores, notas e resultado. Restrições parciais impedem confronto ativo duplicado por encontro e campanha. `Combatant` aceita exatamente uma referência de inimigo ou personagem, guarda snapshots operacionais, PV limitado, ordem/iniciativa, estado narrativo manual, chefe, atividade e nota privada. `HPChange` mantém somente o necessário para desfazer ajustes de PV; `CombatNote` oferece observações narrativas opcionais e não recebe eventos automáticos.

O service transacional de início individualiza cada grupo, aplica overrides de PV/CR/resistência, preserva imagem e chefe, inclui participantes como referência e impede duplicação. Os services de dano e cura limitam PV, aceitam dano final sobrescrito, preservam estados manuais e tornam a derrota em zero opcional. Os limites sugeridos são configuráveis: acima de 50% normal, 26–50% ferido, 1–25% muito ferido e zero derrotado.

## 32.3. Condução, ciclo de vida e interface

Livre oculta turnos. Ordem simples oferece navegação manual sem iniciativa obrigatória. Iniciativa completa ordena em ordem decrescente e incrementa rodada no retorno ao primeiro. Mudanças de modo preservam combatentes. Pausa, retomada, encerramento e reabertura preservam fichas, PV, estados, notas e ordem; encerrar também finaliza o encontro, sem alterar inventário ou história.

A página de encontro oferece “Iniciar confronto” com apenas modo e opção de controlar jogadores. O painel usa HTMX em dano, cura, estado, derrota, reativação, nota, ficha e desfazer, trocando apenas o card ou conteúdo modal. Filtros rápidos e busca apoiam consulta visual. O dashboard prioriza confronto ativo/pausado com “Continuar confronto”, mantendo o navio e ferramentas anteriores acessíveis.

## 32.4. Permissões, condições e auditoria

Todas as views resolvem confronto e combatente dentro de campanha cujo mestre é o usuário autenticado; jogadores recebem 403 mesmo por URL direta. A estrutura preexistente de condições pertence à ficha do personagem e não representa adequadamente estados efêmeros de inimigos; para evitar automação e carga administrativa, esta fase mantém apenas estado narrativo e texto especial curto. Como não existe `ActivityLog`, não foi criada uma segunda auditoria geral: `HPChange` é técnico, discreto e voltado exclusivamente a desfazer PV.

## 32.5. Testes e limitações deliberadas

A suíte da fase cobre individualização, overrides, idempotência, referência exclusiva, faixas de estado, precedência manual, limites de dano/cura, zero ativo, desfazer, ordenação de iniciativa, encerramento/reabertura sem duplicação e autorização. Recursos de jogador são armazenados no snapshot quando selecionados, mas a interface deliberadamente não se torna controle obrigatório; PP/condições continuam sendo geridos na ficha existente. Reordenação visual por arrastar, consumo opcional de ações limitadas e auditoria ampla permanecem melhorias futuras.

---

# 33. Estado implementado — Fase 6 (2026-07-17)

## 33.1. Biblioteca, domínio e uploads

Foi criada a aplicação `audio_panel`. `AudioAsset` pertence obrigatoriamente à campanha, possui slug único nesse escopo, categorias e canais em escolhas estáveis, metadados de personagem/cena/tags, favorito, destaque, ativação lógica, volume de 0 a 1, loop, ordenação e métricas leves. A conversão visual para percentual fica na propriedade `volume_percent`; o player combina volume geral, do canal e do ativo. Índices compostos atendem biblioteca, favoritos, canal, destaque, recentes e uso sem duplicar o índice implícito da FK.

Uploads aceitam MP3, OGG, M4A, WAV e WebM, validando extensão, MIME e o limite `MAX_AUDIO_UPLOAD_SIZE`, agora 100 MiB por padrão. O caminho usa UUID e isolamento em `audio/campaigns/<campaign_id>/`. Não há conversão, normalização, edição, upload pelo player ou integração externa.

## 33.2. Autorização e mídia protegida

Biblioteca, cadastro, edição, desativação, favoritos, registro e arquivo resolvem o objeto apenas entre campanhas do mestre autenticado. Jogadores, anônimos e mestres de outra campanha não obtêm arquivo nem metadados. O fallback de desenvolvimento usa `FileResponse`, mídia inline, `Accept-Ranges`, cache privado sem armazenamento e nunca recebe um caminho do cliente.

Em produção, configure `PROTECTED_MEDIA_MODE=x-accel`, mantenha `MEDIA_ROOT` fora da raiz pública e crie no Nginx uma `location /_protected_media/ { internal; alias /caminho/para/media/; }`, ajustando `PROTECTED_MEDIA_ACCEL_PREFIX` se necessário. A aplicação então autoriza e entrega somente `X-Accel-Redirect`; o Nginx gerencia Range eficientemente.

## 33.3. Player persistente e HTMX

`AudioPanelController` mantém três elementos `Audio`: música, ambiente e efeito/fala. Cada canal toca somente um ativo; efeito não interrompe música ou ambiente. Nova música/ambiente substitui a anterior com transição curta. Há pausa/retomada, parada do canal, parada global, progresso, volume geral, loop padrão e fade cancelável. O fade restaura o volume calculado para a próxima execução.

O componente fica fora das áreas trocadas por HTMX no layout-base do mestre e existe também no combate. Listeners recebem uma marca de inicialização e controles novos são ligados após `htmx:afterSwap`, sem recriar canais. `localStorage` guarda somente preferências de volume, painel recolhido e identificação conveniente do último ativo; URLs privadas e credenciais não são persistidas. Não há autoplay depois de recarga completa.

Atalhos: Espaço pausa/retoma o canal ativo e Ctrl+Shift+S para tudo. Inputs, selects, textareas e editores ignoram atalhos. Escape permanece reservado ao comportamento nativo de modal/offcanvas do Bootstrap.

## 33.4. Biblioteca, favoritos, recentes e dashboard

A biblioteca pagina 24 itens, usa `preload=none` por não criar elementos de mídia até o clique, busca título/tags, filtra categoria/personagem/cena/favorito/atividade e ordena por título, criação ou uso. Favoritar troca somente o botão via HTMX. O registro de início é uma requisição tolerante a falha, incrementa contador atomicamente e atualiza uma única data; pausa e progresso não são registrados. Recentes derivam dessa data, logo cada ativo aparece uma vez.

O dashboard prioriza confronto em andamento e apresenta ações rápidas para encontro, item, navio, mapa, áudio e sessão, com navio, preparados, favoritos de áudio e mapas em blocos compactos. O painel persistente disponibiliza favoritos e recentes em todas as páginas que estendem o layout do mestre, inclusive combate, inimigos, encontros, navio, mapas, história, inventário e fichas.

## 33.5. Divergências e limites deliberados

O projeto já possuía áudio opcional de registro histórico, mas ele representa a gravação da sessão e tem autorização/fluxo próprios; reutilizá-lo como ativo operacional misturaria contratos, portanto foi preservado. Não existia `ActivityLog`, assim criação, edição e desativação não inventam uma auditoria paralela nesta fase. A duração não é processada no servidor: o navegador a conhece somente depois do clique, evitando leitura/download inicial.

O endpoint Django anuncia Range, mas o suporte de produção recomendado e documentado é o Nginx/X-Accel; implementar um servidor binário completo na aplicação duplicaria infraestrutura. Recargas completas inevitavelmente recriam elementos de áudio do navegador; atualizações HTMX não os destroem. O estado conveniente é restaurado sem autoplay, conforme restrições de segurança dos navegadores. Streaming a jogadores, sincronização entre navegadores, múltiplos efeitos simultâneos, playlists complexas, WebSockets, edição, IA e serviços externos permanecem fora do escopo.

## 33.6. Testes

A suíte cobre defaults e validação do modelo, slug por campanha, upload válido, extensão/MIME/tamanho/ausência, autorização de arquivo para mestre/jogador/anônimo/outro mestre, favorito HTMX, registro atômico, ordenação/limite/escopo de recentes e presença exclusiva do painel. Não havia infraestrutura JavaScript de testes; o módulo foi exportado como classe testável e os cenários manuais obrigatórios são: iniciar música, executar dano via HTMX, confirmar continuidade; abrir modal, confirmar continuidade; iniciar fala e confirmar música/ambiente; testar fade e parada global.

---

# 34. Estado implementado — Fase 7 (2026-07-17)

## 34.1. Consolidação e arquitetura Docker

A Fase 7 não altera regras de campanha. Ela consolida os módulos das Fases 1–6 em três serviços isolados na rede `app_network`: Nginx público, Django/Gunicorn interno e PostgreSQL 16 interno. O Dockerfile multi-stage fixa Python 3.12, mantém compiladores apenas no builder, usa usuário `app`, cacheia dependências e nunca inclui `.env`. Desenvolvimento monta o código e publica somente interfaces loopback; produção não monta código nem publica web/db.

## 34.2. Compose, persistência e configuração

`compose.yml` concentra serviços, rede, volumes, dependências saudáveis e rotação de logs; overlays development/production escolhem alvo, comandos, portas, segurança e persistência. Desenvolvimento usa volumes nomeados. Na VPS, banco, mídia e mídia protegida usam bind mounts configuráveis para viabilizar backup fora dos containers; estáticos usam volume compartilhado. Nenhum fluxo operacional remove volumes.

Os settings existentes foram preservados em módulo único para evitar uma migração estrutural desnecessária. Foram acrescentados aliases `DJANGO_*`, CSRF, roots configuráveis, flags de proxy/cookies/HSTS, sessão de seis horas, headers e logging de console. O entrypoint valida segredos em produção, aguarda PostgreSQL por prontidão ativa e não roda migrations/seeds automaticamente.

## 34.3. Nginx, Gunicorn e arquivos

Gunicorn usa 2 workers/2 threads configuráveis, timeout conservador e stdout/stderr. Nginx faz proxy por DNS `web`, serve estáticos e o volume público reservado, aplica limite de 110 MiB e headers, e possui location `internal` para X-Accel. Como os uploads históricos já eram todos autorizados por views, produção aponta `MEDIA_ROOT` ao bind protegido; isso evita expor por engano mapas, inventário, sessões, inimigos ou áudio. O Range fica a cargo do Nginx. TLS segue a opção de certificados do host montados read-only; ativação exige adaptar/validar certificado e então habilitar flags seguras.

## 34.4. Saúde, diagnóstico, segurança e observabilidade

`/health/` é liveness leve e `/health/ready/` verifica banco e diretórios sem revelar exceções. `diagnose_deployment` inspeciona settings, banco, roots, migrations, X-Accel e expectativa HTTPS sem imprimir segredos. Web executa sem root, perde capabilities em produção, usa `no-new-privileges` e tmpfs; nenhum serviço recebe socket Docker. Logs têm limite de 10 MiB e cinco arquivos.

## 34.5. Makefile, deploy e migrations

O Makefile centraliza build, ciclo de vida, shells, checks, testes, seed apenas dev, superusuário explícito, banco, diagnóstico, backups e produção. `deploy.sh` recusa alterações locais, usa `git pull --ff-only`, valida Compose, constrói antes da troca, executa dry-run e geração exigida de migrations, migrate e collectstatic. Migrations geradas na VPS ficam visíveis para revisão/versionamento, sem commit/push. Somente web é recriado e Nginx garantido; db é preservado. `deploy-safe` precede o mesmo fluxo com backup. `DRY_RUN=1` permite simulação não destrutiva.

## 34.6. Backups, boot e operação

Os scripts gravam dump PostgreSQL custom e tar de mídia diretamente em `BACKUP_DIR` do host, aplicam retenção e exigem arquivo mais `CONFIRM_RESTORE=yes` para restauração sem limpeza silenciosa. Exemplos systemd iniciam Compose opcionalmente e agendam backup diário. `OPERATIONS.md` documenta estrutura da VPS, todas as variáveis, SSL, logs, health, deploy, restauração, rollback e troubleshooting.

## 34.7. Limitações e decisões

Não foi implantada CSP porque templates atuais dependem de bibliotecas CDN e comportamentos inline; uma política não testada quebraria HTMX/player. Não há blue-green nem rollback automático de banco. O template padrão entrega HTTP; certificados variam por domínio e a configuração TLS deve ser concluída na VPS antes de HSTS. O healthcheck do Nginx foi omitido para não instalar ferramenta exclusivamente para isso; o smoke externo cobre Nginx. Não foram adicionados IA, Celery, Redis, WebSockets, API, Kubernetes ou regras de domínio.

A verificação inicial encontrou drift entre models e migrations legado. Foram geradas migrations `0002` para accounts, characters, history, inventory, maps e ships, compostas por alinhamento de metadados/campos e renome de índices; nenhuma nova funcionalidade de domínio foi introduzida. Elas foram aplicadas e a verificação posterior retornou `No changes detected`.
## Criação Assistida de Personagens — Livro do Jogador 1.5.7

### Fonte normativa

A criação assistida usa exclusivamente `OP RPG - Livro do Jogador 1.5.7.pdf`, versionado internamente como `player-book-1.5.7`. As decisões de implementação estão registradas em `docs/rules/character_creation_v1_5_7.md`.

### Arquitetura do catálogo

O catálogo é versionado e idempotente. O comando `python manage.py seed_player_book_rules_1_5_7` cadastra atributos, perícias, espécies, variantes, referências de traços Zoan, estilos de combate, profissões, Timoneiro, Sem Profissão, antecedentes, proficiências e dados estruturados de escolhas/equipamentos iniciais.

Models principais:

- `RuleAttribute`: atributos canônicos do OP RPG.
- `Skill`: perícias gerais com atributos canônicos; campos legados continuam para compatibilidade.
- `RuleProficiency`: proficiências versionadas de perícia, salvaguarda, arma, kit, ferramenta e característica.
- `Species` e `SpeciesVariant`: PV base, tamanho, deslocamento, nado, benefícios, dificuldades, traços culturais e escolhas obrigatórias.
- `ZoanAncestryTrait`: referências reutilizáveis para ancestralidades de Mink e Povo do Mar.
- `CombatStyle`: dado de vida, salvaguardas, perícias permitidas, proficiências, atributos primários, arma favorita, habilidade inata, equipamento, dinheiro e características de 1º nível.
- `Profession`: profissões principais, `Sem Profissão` e subprofissão `Timoneiro`.
- `Background`: antecedentes, perícias, atributo recomendado e característica especial.
- `CharacterCreation`: rascunho, etapa atual, pendências, erros, avisos, aprovação do mestre, conceito, idade, altura, peso, caminho e escolhas estruturadas.
- `CharacterAttribute`: decomposição por base, bônus de espécie, bônus de antecedente, outros bônus e valor final.
- `CharacterProficiency`: preserva origem de cada proficiência e evita duplicidade silenciosa.
- `CharacterRuleException`: registra usuário, data, regra ignorada e justificativa.

### Services

- `creation_catalog_service`: consulta opções válidas por versão.
- `character_calculation_service`: funções puras para modificadores, proficiência, PV, CR, iniciativa, carga, perícias, salvaguardas, ataque, dano, pontos raciais e mestiços.
- `character_validation_service`: valida dependências, quantidades de escolhas, limites, variantes, ancestralidade, Timoneiro, Sem Profissão, duplicidade e pendências.
- `choice_dependency_service`: descreve dependências quando uma escolha anterior muda e fornece opções adaptativas.
- `proficiency_resolution_service`: registra proficiências com origem e resolve sobreposição pelo maior multiplicador.
- `equipment_resolution_service`: materializa equipamentos iniciais no inventário.
- `character_creation_service`: cria/atualiza rascunho e confirma a ficha reconstruindo `Character` a partir das escolhas.

### Fluxo e rotas

Jogador:

- `/personagem/<slug>/criar/`: assistente em etapas.
- `/personagem/<slug>/criar/preview/`: prévia HTMX de PV, CR, iniciativa, carga e atributos.
- `/personagem/<slug>/criar/opcoes/`: opções adaptativas HTMX.

Mestre:

- `/mestre/personagens/`: lista/revisão.
- `/mestre/criacoes/<pk>/excecao/`: registra aprovação de exceção.
- `/mestre/criacoes/<pk>/reabrir/`: reabre criação concluída.

Templates:

- `templates/characters/creation/wizard.html`
- `templates/characters/creation/partials/preview.html`
- `templates/characters/creation/partials/options.html`
- `templates/characters/creation/partials/review.html`

HTMX atualiza opções e prévia, mas a confirmação depende sempre de validação no backend.

### Regras implementadas

- Atributos canônicos: Força, Destreza, Constituição, Sabedoria, Vontade e Presença.
- Descrição inicial do personagem: idade, altura, peso e Caminho são preenchidos na etapa Conceito e copiados para a ficha final na confirmação.
- Métodos de atributo: distribuição por pontos, conjunto padrão compatível e geração 4d6 descarta menor. A distribuição por pontos usa total 72, mínimo 8 e máximo 15 antes dos bônus.
- Bônus de espécie/antecedente armazenados separadamente e preenchidos a partir das etapas de espécie e antecedente; a etapa de atributos só edita valores base e mostra os bônus automaticamente.
- Catálogo das 8 espécies, variantes obrigatórias e derivação de mestiço por duas origens.
- Referências de traços Zoan para ancestralidade sem copiar poderes de Akuma no Mi para a ficha.
- Catálogo dos 10 estilos de combate de 1º nível.
- Catálogo das 10 profissões principais, Timoneiro como subprofissão de Navegador e Sem Profissão com restrições.
- Catálogo dos 12 antecedentes, incluindo Nobre com lista conferida no PDF.
- Proficiências com origem e prevenção de soma duplicada. Sobreposição entre estilo, profissão e antecedente é permitida; a origem fica registrada, mas o bônus efetivo entra uma única vez.
- PV inicial, CR, iniciativa, carga, bônus de perícia, salvaguarda, ataque e dano.
- Regras de campanha preservadas: personagem não começa com Akuma no Mi e Haki declarado não libera uso intencional antes de treinamento.

### Ambiguidades e decisões

- Pontos de Treinamento racial por Sabedoria: quando o modificador não é positivo, o serviço retorna 0 e a escolha pode ser aberta após recalcular com Sabedoria positiva.
- Coerência de ancestralidade Zoan: é decisão narrativa do mestre; o sistema exige aprovação para traços específicos/predador quando necessário.
- Requisitos raciais de alguns estilos: ficam representados em JSON e podem ser ignorados por exceção registrada.
- Equipamento de Gigante: a necessidade de adaptação por tamanho é registrada; a materialização detalhada por tamanho fica para evolução do resolvedor de equipamentos, sem progressão pós-1º nível.
- Origem: não foi criado um sistema separado com esse nome. A leitura do livro mantém origem representada por Antecedente e adiciona Caminho como campo específico que faltava na ficha.

### Seeds e testes

Comandos:

```bash
make makemigrations
make migrate
make seed-player-book
make check
make test
```

Testes principais:

- `characters/tests/test_character_creation_rules.py`
- `characters/tests/test_player_campaign_flow.py`

Eles cobrem catálogo, atributos, geração aleatória, mestiços, estilos, profissões, Timoneiro, Sem Profissão, antecedentes, proficiências, derivados, HTMX, permissões, exceção do mestre, isolamento entre campanhas e fluxos completos.
