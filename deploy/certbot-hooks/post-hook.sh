#!/usr/bin/env bash
# Certbot post-hook: restore Nginx container after challenge.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.production"

if [[ -f "$COMPOSE_FILE" && -f "$ENV_FILE" ]]; then
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d nginx || true
fi
