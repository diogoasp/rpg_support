.DEFAULT_GOAL := help
COMPOSE_DEV ?= docker compose -f compose.yml -f compose.development.yml
COMPOSE_PROD ?= docker compose -f compose.yml -f compose.production.yml
WEB_SERVICE ?= web
DB_SERVICE ?= db
NGINX_SERVICE ?= nginx
SERVICE ?=
CMD ?=
TEST_ARGS ?=
.PHONY: help dev-env dev-bootstrap dev dev-rebuild dev-stop dev-logs dev-manage dev-test dev-check dev-db-shell build up down restart logs ps shell django-shell migrate makemigrations showmigrations collectstatic test check check-deploy seed seed-complete seed-player-book seed-level-progression seed-level-up-abilities createsuperuser migrations-check compose-config prod-build prod-up prod-down prod-restart prod-logs prod-ps prod-shell prod-migrate prod-collectstatic prod-check prod-smoke prod-tunnel-up prod-tunnel-down prod-tunnel-logs prod-createsuperuser prod-seed-level-up-abilities prod-migrations-check prod-compose-config deploy deploy-safe db-shell db-backup db-restore backup backup-db backup-media restore-db diagnose prod-diagnose prune-dev
help: ## Lista comandos operacionais
	@awk 'BEGIN {FS=":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "%-28s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
dev-env: ## Cria .env local a partir do exemplo, se ausente
	@test -f .env || cp .env.example .env
dev-bootstrap: dev-env build migrate seed ## Prepara ambiente de desenvolvimento
dev: up logs ## Sobe desenvolvimento e segue logs
dev-rebuild: ## Reconstrói web e recria container de desenvolvimento
	$(COMPOSE_DEV) up -d --build --force-recreate $(WEB_SERVICE)
dev-stop: down ## Para ambiente de desenvolvimento
dev-logs: ## Segue logs do web de desenvolvimento
	$(COMPOSE_DEV) logs -f $(WEB_SERVICE)
dev-manage: ## Executa manage.py CMD="comando" no desenvolvimento
	@test -n "$(CMD)" || (echo 'Use CMD="check" ou CMD="app comando"'; exit 2)
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py $(CMD)
dev-test: ## Executa testes em desenvolvimento (TEST_ARGS opcional)
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py test $(TEST_ARGS)
dev-check: check migrations-check compose-config ## Verifica Django, migrations e Compose de desenvolvimento
dev-db-shell: ## Abre psql no banco de desenvolvimento
	$(COMPOSE_DEV) exec $(DB_SERVICE) psql -U "$${POSTGRES_USER}" -d "$${POSTGRES_DB}"
build: ## Constrói imagem de desenvolvimento
	$(COMPOSE_DEV) build $(WEB_SERVICE)
up: ## Sobe desenvolvimento
	$(COMPOSE_DEV) up -d
down: ## Para desenvolvimento sem remover volumes
	$(COMPOSE_DEV) down
restart: down up ## Reinicia desenvolvimento
logs: ## Segue logs (SERVICE=web opcional)
	$(COMPOSE_DEV) logs -f $(SERVICE)
ps: ## Lista serviços
	$(COMPOSE_DEV) ps
shell: ## Abre shell no web
	$(COMPOSE_DEV) exec $(WEB_SERVICE) sh
django-shell: ## Abre shell Django
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py shell
migrate: ## Aplica migrations em desenvolvimento
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py migrate
makemigrations: ## Gera migrations em desenvolvimento
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py makemigrations
showmigrations: ## Lista migrations
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py showmigrations
collectstatic: ## Coleta estáticos
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py collectstatic --noinput
test: ## Executa testes em container
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py test
check: ## Executa Django check
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py check
check-deploy: ## Executa check de deploy
	$(COMPOSE_DEV) run --rm -e DJANGO_DEBUG=False $(WEB_SERVICE) python manage.py check --deploy
seed: ## Seed idempotente somente no desenvolvimento
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py seed_rpg
seed-complete: ## Carrega o dump completo de deploy/full_database_seed.sql
	$(COMPOSE_DEV) exec -T $(DB_SERVICE) psql -U "$${POSTGRES_USER}" -d "$${POSTGRES_DB}" < deploy/full_database_seed.sql
seed-player-book: ## Seed idempotente do Livro do Jogador 1.5.7
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py seed_player_book_rules_1_5_7
seed-level-progression: ## Seed idempotente da progressão 1-4 do Livro do Jogador 1.5.7
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py seed_level_progression_1_5_7
seed-level-up-abilities: ## Corrige habilidades disponíveis na passagem de nível
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py seed_level_up_basic_abilities_1_5_7
createsuperuser: ## Cria superusuário no desenvolvimento
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py createsuperuser
migrations-check: ## Verifica migrations de desenvolvimento
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) sh -c 'python manage.py makemigrations --check --dry-run && python manage.py migrate --check'
compose-config: ## Valida Compose de desenvolvimento
	$(COMPOSE_DEV) config --quiet
prod-build: ## Constrói imagens de produção
	$(COMPOSE_PROD) build $(WEB_SERVICE)
prod-up: ## Sobe produção
	$(COMPOSE_PROD) up -d
prod-down: ## Para produção sem remover volumes
	$(COMPOSE_PROD) down
prod-restart: ## Recria somente web e garante nginx
	$(COMPOSE_PROD) up -d --build --no-deps $(WEB_SERVICE) && $(COMPOSE_PROD) up -d $(NGINX_SERVICE)
prod-logs: ## Segue logs de produção (SERVICE=web opcional)
	$(COMPOSE_PROD) logs -f $(SERVICE)
prod-ps: ## Lista produção
	$(COMPOSE_PROD) ps
prod-shell: ## Shell no web de produção
	$(COMPOSE_PROD) exec $(WEB_SERVICE) sh
prod-migrate: ## Aplica migrations em produção
	$(COMPOSE_PROD) run --rm $(WEB_SERVICE) python manage.py migrate --noinput
prod-seed-level-up-abilities: ## Corrige habilidades disponíveis na passagem de nível em produção
	$(COMPOSE_PROD) run --rm $(WEB_SERVICE) python manage.py seed_level_up_basic_abilities_1_5_7
prod-collectstatic: ## Coleta estáticos em produção
	$(COMPOSE_PROD) run --rm $(WEB_SERVICE) python manage.py collectstatic --noinput
prod-check: ## Django check de produção
	$(COMPOSE_PROD) run --rm $(WEB_SERVICE) python manage.py check --deploy
prod-smoke: ## Executa smoke test
	./deploy/smoke_test.sh
prod-tunnel-up: ## Sobe Cloudflare Tunnel de produção
	COMPOSE_PROFILES=tunnel $(COMPOSE_PROD) up -d cloudflared
prod-tunnel-down: ## Para Cloudflare Tunnel de produção
	COMPOSE_PROFILES=tunnel $(COMPOSE_PROD) stop cloudflared
prod-tunnel-logs: ## Segue logs do Cloudflare Tunnel
	COMPOSE_PROFILES=tunnel $(COMPOSE_PROD) logs -f cloudflared
prod-createsuperuser: ## Cria superusuário explicitamente em produção
	$(COMPOSE_PROD) run --rm $(WEB_SERVICE) python manage.py createsuperuser
prod-migrations-check: ## Verifica migrations em produção
	$(COMPOSE_PROD) run --rm $(WEB_SERVICE) sh -c 'python manage.py makemigrations --check --dry-run && python manage.py migrate --check'
prod-compose-config: ## Valida Compose de produção
	$(COMPOSE_PROD) config --quiet
deploy: ## Deploy protegido (DRY_RUN=1 simula)
	./deploy/deploy.sh
deploy-safe: backup deploy ## Backup seguido de deploy
backup: ## Backup completo
	./deploy/backup_all.sh
backup-db db-backup: ## Backup PostgreSQL
	./deploy/backup_database.sh
backup-media: ## Backup das mídias
	./deploy/backup_media.sh
restore-db db-restore: ## Restaura FILE=... com CONFIRM_RESTORE=yes
	@test -n "$(FILE)" || (echo 'Use FILE=/caminho/backup.dump'; exit 2)
	FILE="$(FILE)" ./deploy/restore_database.sh
db-shell: ## Abre psql
	$(COMPOSE_PROD) exec $(DB_SERVICE) psql -U "$${POSTGRES_USER}" -d "$${POSTGRES_DB}"
diagnose: ## Diagnóstico em desenvolvimento
	$(COMPOSE_DEV) run --rm $(WEB_SERVICE) python manage.py diagnose_deployment
prod-diagnose: ## Diagnóstico em produção
	$(COMPOSE_PROD) run --rm $(WEB_SERVICE) python manage.py diagnose_deployment
prune-dev: ## Remove somente containers/imagens órfãos do projeto, nunca volumes
	$(COMPOSE_DEV) down --remove-orphans && docker image prune -f --filter label=com.docker.compose.project=$${COMPOSE_PROJECT_NAME:-onepiece-rpg}
