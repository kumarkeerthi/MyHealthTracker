#!/usr/bin/env bash
# Certbot pre-hook: prevent port 80/443 conflicts by stopping Nginx container.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.production"

if [[ -f "$COMPOSE_FILE" && -f "$ENV_FILE" ]]; then
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop nginx || true
fi
