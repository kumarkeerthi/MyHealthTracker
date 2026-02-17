#!/usr/bin/env bash
# Dry-run validation of deployment prerequisites and runtime behavior.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.production"

log() { printf '[dry-run] %s\n' "$*"; }
die() { printf '[dry-run][error] %s\n' "$*" >&2; exit 1; }

[[ -f "$ENV_FILE" ]] || die "Missing .env.production"

set -a
# shellcheck disable=SC1091
source "$ENV_FILE"
set +a

: "${DOMAIN:?DOMAIN missing from .env.production}"

log "Check 1/6: Docker daemon is running"
docker info >/dev/null

log "Check 2/6: Compose file is valid"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config >/dev/null

log "Check 3/6: Services can be started"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d db redis backend frontend nginx

log "Check 4/6: Nginx responds on HTTP"
curl -fsS "http://127.0.0.1/health" >/dev/null

log "Check 5/6: Certbot dry-run renewal executes"
sudo certbot renew --dry-run \
  --pre-hook "$PROJECT_DIR/deploy/certbot-hooks/pre-hook.sh" \
  --post-hook "$PROJECT_DIR/deploy/certbot-hooks/post-hook.sh" \
  --deploy-hook "$PROJECT_DIR/deploy/certbot-hooks/deploy-hook.sh"

log "Check 6/6: SSL endpoint is reachable"
curl -kfsS "https://${DOMAIN}/health" >/dev/null

log "Dry-run checks completed successfully"
