#!/usr/bin/env bash
# Quick rollback helper: restart stack from a selected git commit.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.production"
TARGET_REF="${1:-}"

log() { printf '[rollback] %s\n' "$*"; }
die() { printf '[rollback][error] %s\n' "$*" >&2; exit 1; }

[[ -n "$TARGET_REF" ]] || die "Usage: ./rollback.sh <git-ref>"
[[ -f "$ENV_FILE" ]] || die "Missing $ENV_FILE"

log "Checking out $TARGET_REF"
git fetch --all --tags
git checkout "$TARGET_REF"

log "Rebuilding and restarting stack from $TARGET_REF"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build --remove-orphans

log "Rollback finished. Validate: curl -kfsS https://$(awk -F= '/^DOMAIN=/{print $2}' "$ENV_FILE")/health"
