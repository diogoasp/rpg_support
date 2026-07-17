#!/bin/sh
set -eu
COMPOSE_PROD=${COMPOSE_PROD:-"docker compose -f compose.yml -f compose.production.yml"}
BACKUP_DIR=${BACKUP_DIR:-./data/backups}; RETENTION=${BACKUP_RETENTION_DAYS:-14}
mkdir -p "$BACKUP_DIR"; file="$BACKUP_DIR/database_$(date -u +%Y%m%dT%H%M%SZ).dump"
sh -c "$COMPOSE_PROD exec -T db pg_dump -U \"\${POSTGRES_USER}\" -d \"\${POSTGRES_DB}\" -Fc" > "$file"
find "$BACKUP_DIR" -type f -name 'database_*.dump' -mtime "+$RETENTION" -delete
printf 'Backup do banco: %s\n' "$file"
