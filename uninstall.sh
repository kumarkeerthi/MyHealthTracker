#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"

read -rp "This will stop and remove deployed containers and volumes. Continue? (type YES): " CONFIRM
[[ "$CONFIRM" == "YES" ]] || { echo "Aborted."; exit 0; }

if [[ -f "$COMPOSE_FILE" ]]; then
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down -v --remove-orphans || true
fi

read -rp "Remove generated secrets and SSL artifacts from ./deploy? (Y/N): " CLEAN_DEPLOY
CLEAN_DEPLOY="$(echo "$CLEAN_DEPLOY" | tr '[:lower:]' '[:upper:]')"
if [[ "$CLEAN_DEPLOY" == "Y" ]]; then
  rm -rf deploy/secrets deploy/letsencrypt deploy/certbot-www deploy/nginx.conf
fi

read -rp "Remove .env file? (Y/N): " CLEAN_ENV
CLEAN_ENV="$(echo "$CLEAN_ENV" | tr '[:lower:]' '[:upper:]')"
if [[ "$CLEAN_ENV" == "Y" ]]; then
  rm -f .env
fi

echo "Uninstall complete."
