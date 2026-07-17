#!/bin/sh
set -eu
BACKUP_DIR=${BACKUP_DIR:-./data/backups}; MEDIA_DATA_DIR=${MEDIA_DATA_DIR:-./data/media}; PROTECTED_MEDIA_DATA_DIR=${PROTECTED_MEDIA_DATA_DIR:-./data/protected_media}; RETENTION=${BACKUP_RETENTION_DAYS:-14}
mkdir -p "$BACKUP_DIR" "$MEDIA_DATA_DIR" "$PROTECTED_MEDIA_DATA_DIR"
file="$BACKUP_DIR/media_$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
tar -czf "$file" "$MEDIA_DATA_DIR" "$PROTECTED_MEDIA_DATA_DIR"
find "$BACKUP_DIR" -type f -name 'media_*.tar.gz' -mtime "+$RETENTION" -delete
printf 'Backup de mídia: %s\n' "$file"
