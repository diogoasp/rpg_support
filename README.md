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
