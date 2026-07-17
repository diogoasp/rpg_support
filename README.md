# Grand Line Companion — Fase 1

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

A aplicação inclui ficha operacional do navio, biblioteca de mapas com visibilidade global ou específica e histórico publicável das sessões. Execute `python manage.py seed_rpg` para criar dados demonstrativos idempotentes.

Uploads são armazenados em `media/ships`, `media/maps` e `media/history`. Mapas e áudios são entregues por views autenticadas; em produção, mantenha `MEDIA_ROOT` fora da raiz pública e use Nginx interno/X-Accel conforme descrito em `documentação.md`.

| Variável | Descrição / padrão |
| --- | --- |
| `MAX_IMAGE_UPLOAD_SIZE` | Limite de imagem em bytes (10 MiB sugeridos) |
| `MAX_DOCUMENT_UPLOAD_SIZE` | Limite de PDF em bytes (20 MiB) |
| `MAX_AUDIO_UPLOAD_SIZE` | Limite de áudio em bytes (250 MiB) |
| `PROTECTED_MEDIA_MODE` | `django` no desenvolvimento; reservado para integração com servidor web em produção |
