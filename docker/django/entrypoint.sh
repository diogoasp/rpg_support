#!/bin/sh
set -eu
: "${DJANGO_SETTINGS_MODULE:=config.settings}"
if [ "${DJANGO_DEBUG:-False}" != "True" ]; then
  : "${DJANGO_SECRET_KEY:?DJANGO_SECRET_KEY is required in production}"
  : "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required in production}"
fi
mkdir -p "${STATIC_ROOT:-/app/staticfiles}" "${MEDIA_ROOT:-/app/media}" "${PROTECTED_MEDIA_ROOT:-/app/protected_media}"
if [ -n "${POSTGRES_HOST:-}" ]; then
  echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."
  until nc -z "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}"; do sleep 1; done
fi
exec "$@"
