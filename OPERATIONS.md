# Operação — Fase 7

## Arquitetura

A imagem Python 3.12 possui estágios `development` e `production`, executa como usuário `app` não root e envia logs do Django/Gunicorn para stdout. A rede `app_network` liga `nginx → web:8000 → db:5432`; apenas Nginx publica porta em produção. PostgreSQL 16 possui `pg_isready`; web usa health HTTP e também aguarda a porta do banco no entrypoint. Logs `json-file` rotacionam em 10 MiB/5 arquivos.

## Persistência e host

Na VPS recomenda-se `/srv/onepiece-rpg/{app,env,data,certificates}`. Clone em `app`, proteja `env/production.env` (ou `.env`) com modo 600 e defina caminhos absolutos para `POSTGRES_DATA_DIR`, `MEDIA_DATA_DIR`, `PROTECTED_MEDIA_DATA_DIR`, `BACKUP_DIR` e `CERTIFICATES_DIR`. Produção usa bind mounts para banco/mídia (backup simples) e volume nomeado `static_data`. O deploy nunca usa `down -v` e recria apenas web/nginx.

Arquivos de domínio existentes são privados: em produção `MEDIA_ROOT` aponta para o bind protegido. Django autoriza cada objeto e emite X-Accel; Nginx entrega pela location `internal`, incluindo Range nativo para MP3/M4A/OGG/arquivos grandes. `/media/` fica reservado para futura mídia realmente pública e não contém uploads privados.

## Ambiente

Copie `.env.example`, substitua ambos os segredos, hosts e origens. Em produção use `DJANGO_DEBUG=False`, `PROTECTED_MEDIA_MODE=x-accel` e `X_ACCEL_REDIRECT_ENABLED=True`. Ative redirect/cookies seguros e HSTS **somente após** validar HTTPS. `NGINX_CLIENT_MAX_BODY_SIZE` (110m padrão) deve ser pelo menos o maior limite Django. Workers/threads começam em 2/2; aumente somente após observar RAM/CPU.

## Desenvolvimento e produção

`make help` lista a interface. Fluxo dev: `make build up migrate seed`; testes: `make test check migrations-check`. Produção inicial: `make prod-build prod-up prod-migrate prod-collectstatic prod-check prod-smoke`. Use `SERVICE=web make prod-logs`, `make prod-ps`, `make prod-shell` e `make prod-diagnose` para diagnóstico.

## Deploy e migrations

`make deploy` recusa working tree suja, usa `git pull --ff-only`, valida Compose, constrói antes da troca, faz dry-run e depois `makemigrations` (requisito do projeto), `migrate`, `collectstatic`, recria somente `web`, garante `nginx` e roda smoke. Migration gerada na VPS é exibida e deve ser revisada/versionada no desenvolvimento; nunca há commit/push automático. `DRY_RUN=1 make deploy` valida o roteiro sem alterar Git/containers. Migrations incompatíveis requerem janela de manutenção. Prefira `make deploy-safe` para backup prévio.

## Backup e restauração

`make backup` gera dump custom do PostgreSQL e tar das duas árvores de mídia no host, com retenção configurável. O timer systemd de exemplo executa-o diariamente. Restaure após backup recente e janela de manutenção com `CONFIRM_RESTORE=yes make restore-db FILE=/caminho/database.dump`; o script não apaga objetos automaticamente. Teste restaurações periodicamente em ambiente separado.

## SSL, boot e health

A estratégia padrão monta certificados do host somente leitura; adapte um server TLS ao template antes de habilitar flags HTTPS. Certificados nunca entram na imagem. O serviço systemd Compose é opcional quando Docker e `restart: unless-stopped` já iniciam no boot; substitua placeholders. `/health/` é liveness sem banco, `/health/ready/` verifica banco/diretórios, e o smoke também consulta login. Nginx usa ferramentas nativas e não ganhou healthcheck próprio para evitar dependência extra.

## Rollback e troubleshooting

Faça backup, identifique commit conhecido, confirme compatibilidade do schema, faça checkout explícito, `make prod-build`, recrie somente web, colete estáticos e rode smoke. Não automatize rollback do banco. Em falhas: `make prod-compose-config`, `make prod-ps`, `SERVICE=web make prod-logs`, `make prod-diagnose`; cheque permissões UID 1000 nos bind mounts, DNS `db`/`web`, espaço e certificado. Nunca use reset/clean automáticos nem remova volumes.
