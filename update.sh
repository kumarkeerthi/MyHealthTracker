#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

ENV_FILE=".env"
COMPOSE_FILE="docker-compose.prod.yml"

log() { printf "\n[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die() { printf "\n[ERROR] %s\n" "$*"; exit 1; }

[[ -f "$ENV_FILE" ]] || die "Missing .env. Run deploy.sh first."
[[ -f "$COMPOSE_FILE" ]] || die "Missing docker-compose.prod.yml."

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

POSTGRES_USER="${POSTGRES_USER:-metabolic_user}"
POSTGRES_DB="${POSTGRES_DB:-metabolic_db}"

log "Updating images and restarting services..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull || true
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build --remove-orphans

DOMAIN="$(awk -F= '/^DOMAIN=/{print $2}' "$ENV_FILE")"
[[ -n "$DOMAIN" ]] || die "DOMAIN is not set in .env."

log "Running post-update health checks..."
curl -fsS "https://${DOMAIN}/api/health" >/dev/null
curl -fsS "https://${DOMAIN}" >/dev/null

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" >/dev/null

log "Update completed successfully."
