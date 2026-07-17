#!/bin/sh
set -eu
COMPOSE_PROD=${COMPOSE_PROD:-"docker compose -f compose.yml -f compose.production.yml"}
step() { printf '\n==> %s\n' "$1"; }
step "Verificando árvore de trabalho"
if [ -n "$(git status --porcelain)" ]; then echo "Deploy interrompido: há alterações locais." >&2; exit 1; fi
if [ "${DRY_RUN:-0}" = 1 ]; then
  step "Simulação segura: git pull --ff-only; config; build; makemigrations; migrate; collectstatic; recriar web/nginx; smoke"
  exit 0
fi
step "Atualizando código"; git pull --ff-only
step "Validando Compose"; sh -c "$COMPOSE_PROD config --quiet"
step "Construindo web"; sh -c "$COMPOSE_PROD build web"
step "Verificando migrations"; sh -c "$COMPOSE_PROD run --rm web python manage.py makemigrations --check --dry-run" || echo "Novas migrations são necessárias."
before=$(git status --porcelain -- '*/migrations/*.py')
step "Gerando migrations exigidas pelo fluxo"; sh -c "$COMPOSE_PROD run --rm web python manage.py makemigrations"
after=$(git status --porcelain -- '*/migrations/*.py')
[ "$before" = "$after" ] || { echo "ATENÇÃO: migrations foram geradas na VPS; revise e versione-as no desenvolvimento:"; printf '%s\n' "$after"; }
step "Aplicando migrations"; sh -c "$COMPOSE_PROD run --rm web python manage.py migrate --noinput"
step "Coletando estáticos"; sh -c "$COMPOSE_PROD run --rm web python manage.py collectstatic --noinput"
step "Recriando somente web e garantindo nginx"; sh -c "$COMPOSE_PROD up -d --build --no-deps web"; sh -c "$COMPOSE_PROD up -d nginx"
step "Smoke test"; ./deploy/smoke_test.sh
step "Status final"; sh -c "$COMPOSE_PROD ps"
