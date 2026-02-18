#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ROOT_DIR}/.env.production"
DOMAIN="${APP_DOMAIN:-${DOMAIN:-}}"
EMAIL="${LETSENCRYPT_EMAIL:-admin@${DOMAIN:-example.com}}"

log(){ echo "[setup-https] $*"; }
fail(){ echo "[setup-https][error] $*" >&2; exit 1; }
require_cmd(){ command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"; }
port_free(){ ! ss -ltn "( sport = :$1 )" | rg -q ":$1\b"; }
random_secret(){ openssl rand -base64 48 | tr -d '\n'; }

[[ -n "$DOMAIN" ]] || fail "Set APP_DOMAIN (or DOMAIN) before running setup-https.sh"

require_cmd docker
require_cmd openssl
require_cmd nginx
require_cmd certbot
require_cmd curl
require_cmd rg
require_cmd ss

for p in 80 443; do
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

set_kv ENV production
set_kv ENVIRONMENT production
set_kv REQUIRE_HTTPS true
set_kv CORS_ALLOWED_ORIGINS "https://${DOMAIN}"
set_kv NEXT_PUBLIC_API_BASE_URL "https://${DOMAIN}"
set_kv APP_DOMAIN "$DOMAIN"
set_kv DOMAIN "$DOMAIN"

for key in POSTGRES_PASSWORD REDIS_PASSWORD JWT_SECRET HEALTH_SYNC_SIGNING_SECRET; do
  current="$(awk -F= -v k="$key" '$1==k{print $2}' "$ENV_FILE" | tail -n1)"
  if [[ -z "$current" || "$current" == CHANGE_ME* ]]; then
    set_kv "$key" "$(random_secret)"
  fi
done

POSTGRES_USER="$(awk -F= '$1=="POSTGRES_USER"{print $2}' "$ENV_FILE" | tail -n1)"
POSTGRES_DB="$(awk -F= '$1=="POSTGRES_DB"{print $2}' "$ENV_FILE" | tail -n1)"
POSTGRES_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print $2}' "$ENV_FILE" | tail -n1)"
REDIS_PASSWORD="$(awk -F= '$1=="REDIS_PASSWORD"{print $2}' "$ENV_FILE" | tail -n1)"
set_kv DATABASE_URL "postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}"
set_kv REDIS_URL "redis://:${REDIS_PASSWORD}@redis:6379/0"
set_kv CELERY_BROKER_URL "redis://:${REDIS_PASSWORD}@redis:6379/0"
set_kv CELERY_RESULT_BACKEND "redis://:${REDIS_PASSWORD}@redis:6379/0"

log "Deploying containers"
cd "$ROOT_DIR"
docker compose down -v || true
docker compose up -d --build

log "Writing nginx reverse proxy config"
sudo tee /etc/nginx/sites-available/myhealthtracker >/dev/null <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF
sudo ln -sf /etc/nginx/sites-available/myhealthtracker /etc/nginx/sites-enabled/myhealthtracker
sudo nginx -t
sudo systemctl reload nginx

log "Requesting/renewing Let's Encrypt certificate"
sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect

log "Validating backend health"
for _ in {1..60}; do
  if curl -fsS "https://${DOMAIN}/health" >/dev/null; then
    log "HTTPS setup complete. Backend healthy at https://${DOMAIN}/health"
    exit 0
  fi
  sleep 2
done

fail "Backend did not become healthy in time over HTTPS. Check nginx/certbot and container logs."
