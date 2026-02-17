#!/usr/bin/env bash
# Certbot deploy-hook: sync renewed certs and reload Nginx.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.production"

rsync -a /etc/letsencrypt/ "$PROJECT_DIR/deploy/letsencrypt/"

if [[ -f "$COMPOSE_FILE" && -f "$ENV_FILE" ]]; then
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T nginx nginx -s reload || true
fi
