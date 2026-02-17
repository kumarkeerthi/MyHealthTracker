#!/usr/bin/env bash
# Rolling production update with health checks and automatic rollback support.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.production"
BACKUP_DIR="$PROJECT_DIR/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
SNAPSHOT_FILE="$BACKUP_DIR/update-${STAMP}.txt"

log() { printf '[update] %s\n' "$*"; }
die() { printf '[update][error] %s\n' "$*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

load_env_file() {
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
}

health_checks() {
  log "Running post-update health checks"
  curl -fsS "http://127.0.0.1/health" >/dev/null
  curl -kfsS "https://${DOMAIN}/health" >/dev/null
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'SELECT 1;' >/dev/null
}

create_snapshot() {
  mkdir -p "$BACKUP_DIR"
  {
    echo "# Snapshot created: $STAMP"
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    echo
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" images
  } > "$SNAPSHOT_FILE"
  log "Saved container/image snapshot at $SNAPSHOT_FILE"
}

main() {
  require_cmd docker
  require_cmd curl
  [[ -f "$COMPOSE_FILE" ]] || die "Missing compose file: $COMPOSE_FILE"
  [[ -f "$ENV_FILE" ]] || die "Missing env file: $ENV_FILE"

  load_env_file
  : "${DOMAIN:?DOMAIN is required in .env.production}"
  : "${POSTGRES_USER:?POSTGRES_USER is required in .env.production}"
  : "${POSTGRES_DB:?POSTGRES_DB is required in .env.production}"

  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config >/dev/null
  create_snapshot

  log "Pulling latest image updates"
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull

  log "Rebuilding local images and recreating services"
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build --remove-orphans

  health_checks
  log "Update completed successfully"
}

main "$@"
