FROM python:3.12.10-slim-bookworm AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev libjpeg-dev zlib1g-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.12.10-slim-bookworm AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/opt/venv/bin:$PATH
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 libjpeg62-turbo netcat-openbsd && rm -rf /var/lib/apt/lists/* \
 && groupadd --gid 1000 app && useradd --uid 1000 --gid app --create-home app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app . .
RUN mkdir -p /app/staticfiles /app/media /app/protected_media /tmp/app && chown -R app:app /app/staticfiles /app/media /app/protected_media /tmp/app \
 && chmod +x /app/docker/django/*.sh
USER app
ENTRYPOINT ["/app/docker/django/entrypoint.sh"]

FROM base AS development
CMD ["/app/docker/django/start-development.sh"]
FROM base AS production
CMD ["/app/docker/django/start-production.sh"]
