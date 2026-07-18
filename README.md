# Grand Line Companion — Fase 7

Fundação de um sistema Django para apoio presencial a campanhas de RPG. Esta fase inclui autenticação, usuários com papéis de mestre e jogador, campanhas, autorização no backend e dashboards separados.

## Requisitos

- Python 3.12+
- PostgreSQL

## Instalação local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Crie o banco e usuário indicados em `DATABASE_URL` no `.env`, depois execute:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Ao criar usuários pelo admin (`/admin/`), selecione o papel **Mestre** ou **Jogador**. Mestres podem criar campanhas pela interface e associar jogadores já cadastrados.

## Testes

Os testes usam SQLite isoladamente, portanto não precisam do PostgreSQL local:

```bash
python manage.py test
```

## Configuração

| Variável | Descrição |
| --- | --- |
| `SECRET_KEY` | Segredo criptográfico do Django |
| `DEBUG` | Ativa o modo de desenvolvimento |
| `ALLOWED_HOSTS` | Hosts separados por vírgula |
| `DATABASE_URL` | URL de conexão PostgreSQL |

## Fase 3 — navio, mapas e história

A aplicação inclui ficha operacional do navio, biblioteca de mapas com visibilidade global ou específica e histórico publicável das sessões. Execute `python manage.py seed_rpg` para criar dados idempotentes de desenvolvimento, incluindo a campanha `Tambores da Libertação` e a `Caravela revolucionária de apoio`.

Uploads são armazenados em `media/ships`, `media/maps` e `media/history`. Mapas e áudios são entregues por views autenticadas; em produção, mantenha `MEDIA_ROOT` fora da raiz pública e use Nginx interno/X-Accel conforme descrito em `documentação.md`.

| Variável | Descrição / padrão |
| --- | --- |
| `MAX_IMAGE_UPLOAD_SIZE` | Limite de imagem em bytes (10 MiB sugeridos) |
| `MAX_DOCUMENT_UPLOAD_SIZE` | Limite de PDF em bytes (20 MiB) |
| `MAX_AUDIO_UPLOAD_SIZE` | Limite de áudio em bytes (250 MiB) |
| `PROTECTED_MEDIA_MODE` | `django` no desenvolvimento; reservado para integração com servidor web em produção |
| `MAX_ENEMY_IMAGE_UPLOAD_SIZE` | Limite de imagens privadas do catálogo (5 MiB) |

## Fase 4 — inimigos e encontros preparados

O mestre dispõe de catálogo global reutilizável em `/mestre/inimigos/` e, no card de cada campanha, do gerador de encontros. O gerador considera participantes, dificuldade, quantidade, chefe, facção, ambiente e inimigo obrigatório; sua proposta é editável por HTMX e só é persistida após confirmação como rascunho ou preparada. A estimativa é deliberadamente orientativa e não inicia combate.

Para criar/atualizar os dados fictícios idempotentes das Fases 1–4:

```bash
python manage.py seed_rpg
```


## Fase 5 — painel narrativo de combate

Encontros preparados agora podem ser iniciados no modo Livre (padrão), Ordem simples ou Iniciativa completa. O painel exclusivo do mestre individualiza inimigos, oferece dano, cura, estados narrativos, notas, ficha rápida, desfazer PV, pausa, retomada e encerramento com atualizações HTMX compactas. Ele é um apoio presencial e não executa ataques, rolagens ou movimentação tática.

## Fase 6 — áudio e dashboard operacional

A biblioteca privada em `/mestre/audios/` organiza músicas, ambientes, efeitos e falas por campanha. O painel inferior exclusivo do mestre mantém três canais locais independentes, favoritos, recentes, pausa, parada, volume, loop e fade durante atualizações HTMX. O dashboard prioriza confronto ativo e reúne atalhos de sessão para encontro, inventário, navio, mapas, histórico e áudio.

Atalhos do player: `Espaço` pausa/retoma o canal ativo e `Ctrl+Shift+S` para todos os canais. Eles são ignorados dentro de campos de formulário. Por restrições dos navegadores, uma recarga completa não inicia nem retoma áudio automaticamente; preferências de volume e abertura do painel são restauradas localmente.

## Fase 7 — execução por containers

A operação suportada agora usa Docker Compose; Python e PostgreSQL no host deixaram de ser requisitos. Copie o exemplo de ambiente e nunca versione o `.env`:

```bash
cp .env.example .env
make build
make up
make migrate
make seed
```

Testes e verificações usam `make test` e `make check`. Para uma primeira subida de produção, configure segredos/domínio no `.env` da VPS e execute:

```bash
make prod-build
make prod-up
make prod-migrate
make prod-collectstatic
make prod-smoke
```

Atualizações normais usam `make deploy`; a opção recomendada na VPS é `make deploy-safe`, que cria backups antes. Consulte [OPERATIONS.md](OPERATIONS.md) para SSL, volumes, restauração, rollback e troubleshooting. O banco e o Gunicorn não possuem portas públicas em produção; somente o Nginx é publicado.

## Livro do Jogador 1.5.7 — criação assistida

O catálogo oficial usado pelo assistente é versionado como `player-book-1.5.7`. Para cadastrar ou atualizar atributos, perícias, espécies, variantes, estilos, profissões, antecedentes, proficiências, características e equipamentos iniciais:

```bash
make seed-player-book
```

O jogador inicia a criação pela seleção de campanha no painel e acessa:

```text
/personagem/<slug-da-campanha>/criar/
```

O assistente salva rascunho por etapas: conceito, espécie, estilo, profissão, atributos, antecedente, personalidade, pendências, equipamentos e revisão. A etapa Conceito registra nome, conceito, idade, altura, peso e Caminho. A etapa de atributos distribui 72 pontos, com mínimo 8 e máximo 15 antes dos bônus; bônus raciais e de antecedente são definidos nas etapas correspondentes e aparecem automaticamente na prévia. A ficha final só é criada na confirmação.

O mestre revisa personagens em `/mestre/personagens/`. Exceções de regra ficam registradas com usuário, data, regra ignorada e justificativa em `CharacterRuleException`.
