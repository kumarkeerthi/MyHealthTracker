#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ROOT_DIR}/.env.production"

log(){ echo "[setup-http] $*"; }
fail(){ echo "[setup-http][error] $*" >&2; exit 1; }
require_cmd(){ command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"; }
port_free(){ ! ss -ltn "( sport = :$1 )" | rg -q ":$1\b"; }
random_secret(){ openssl rand -base64 48 | tr -d '\n'; }

require_cmd docker
require_cmd openssl
require_cmd ss
require_cmd rg

IP="${HOST_IP:-$(hostname -I | awk '{print $1}') }"
[[ -n "$IP" ]] || fail "Unable to detect host IP. Set HOST_IP and retry."

for p in 3000 8000 5432 6379; do
  if ! port_free "$p"; then
    fail "Port ${p} is already in use. Stop conflicting services before continuing."
  fi
done

if [[ ! -f "$ENV_FILE" ]]; then
  cp "${ROOT_DIR}/.env.example" "$ENV_FILE"
  log "Created ${ENV_FILE} from .env.example"
fi

set_kv(){
  local key="$1" val="$2"
  if rg -q "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
  else
    echo "${key}=${val}" >> "$ENV_FILE"
  fi
}

set_kv ENV development
set_kv ENVIRONMENT development
set_kv REQUIRE_HTTPS false
set_kv CORS_ALLOWED_ORIGINS "http://${IP}:3000"
set_kv NEXT_PUBLIC_API_BASE_URL "http://${IP}:8000"

for key in POSTGRES_PASSWORD REDIS_PASSWORD JWT_SECRET HEALTH_SYNC_SIGNING_SECRET; do
  current="$(awk -F= -v k="$key" '$1==k{print $2}' "$ENV_FILE" | tail -n1)"
  if [[ -z "$current" || "$current" == CHANGE_ME* ]]; then
    set_kv "$key" "$(random_secret)"
  fi
done

# Keep DATABASE_URL/REDIS URLs coherent with password and db defaults
POSTGRES_USER="$(awk -F= '$1=="POSTGRES_USER"{print $2}' "$ENV_FILE" | tail -n1)"
POSTGRES_DB="$(awk -F= '$1=="POSTGRES_DB"{print $2}' "$ENV_FILE" | tail -n1)"
POSTGRES_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print $2}' "$ENV_FILE" | tail -n1)"
REDIS_PASSWORD="$(awk -F= '$1=="REDIS_PASSWORD"{print $2}' "$ENV_FILE" | tail -n1)"
set_kv DATABASE_URL "postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}"
set_kv REDIS_URL "redis://:${REDIS_PASSWORD}@redis:6379/0"
set_kv CELERY_BROKER_URL "redis://:${REDIS_PASSWORD}@redis:6379/0"
set_kv CELERY_RESULT_BACKEND "redis://:${REDIS_PASSWORD}@redis:6379/0"

cd "$ROOT_DIR"
log "Starting clean HTTP deployment"
docker compose down -v || true
docker compose up -d --build

log "Waiting for health endpoint"
for _ in {1..60}; do
  if curl -fsS "http://localhost:8000/health" >/dev/null; then
    log "HTTP setup complete. Backend healthy at http://localhost:8000/health"
    exit 0
  fi
  sleep 2
done

fail "Backend did not become healthy in time. Check: docker compose logs backend"
