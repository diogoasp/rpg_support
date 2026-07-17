#!/bin/sh
set -eu
: "${FILE:?Informe FILE=/caminho/backup.dump}"
[ -f "$FILE" ] || { echo "Arquivo inexistente: $FILE" >&2; exit 2; }
[ "${CONFIRM_RESTORE:-no}" = yes ] || { echo "Restauração altera o banco. Reexecute com CONFIRM_RESTORE=yes." >&2; exit 2; }
COMPOSE_PROD=${COMPOSE_PROD:-"docker compose -f compose.yml -f compose.production.yml"}
echo "Restaurando backup explicitamente informado (objetos existentes não serão apagados automaticamente)."
sh -c "$COMPOSE_PROD exec -T db pg_restore -U \"\${POSTGRES_USER}\" -d \"\${POSTGRES_DB}\" --no-owner --no-privileges" < "$FILE"
