#!/usr/bin/env bash
# Production/local deployment entrypoint for MyHealthTracker.
# This script is safe to re-run and logs every major step.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/setup.log"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.production"
DOMAIN=""
LETSENCRYPT_EMAIL=""
MODE="production"
SKIP_DNS_CHECK="false"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

log() { printf '[setup] %s\n' "$*"; }
warn() { printf '[setup][warn] %s\n' "$*"; }
die() { printf '[setup][error] %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'USAGE'
Usage:
  ./setup.sh --production [--env-file .env.production] [--skip-dns-check]
  ./setup.sh --local

Notes:
- --production prepares Docker services, provisions Let's Encrypt certs,
  renders the final Nginx config, and enables auto-renewal with systemd.
- --local starts the developer compose stack.
USAGE
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

load_env_file() {
  local file="$1"
  [[ -f "$file" ]] || die "Missing env file: $file"
  set -a
  # shellcheck disable=SC1090
  source "$file"
  set +a
}

ensure_docker_running() {
  require_cmd docker
  if docker info >/dev/null 2>&1; then
    return 0
  fi

  if command -v systemctl >/dev/null 2>&1; then
    log "Docker daemon is not running. Attempting to start docker.service..."
    sudo systemctl start docker || die "Failed to start docker.service"
    sleep 2
    docker info >/dev/null 2>&1 || die "Docker daemon still unavailable after systemctl start"
  else
    die "Docker daemon is not running and systemctl is unavailable"
  fi
}

ensure_compose_v2() {
  docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required (docker compose)"
}

render_nginx_config() {
  local template="$PROJECT_DIR/deploy/nginx.template.conf"
  local output="$PROJECT_DIR/deploy/nginx.conf"

  [[ -f "$template" ]] || die "Missing nginx template: $template"
  sed "s|__APP_DOMAIN__|${DOMAIN}|g" "$template" > "$output"
  log "Rendered Nginx config: $output"
}

render_http_only_nginx_config() {
  local template="$PROJECT_DIR/deploy/nginx.http-only.template.conf"
  local output="$PROJECT_DIR/deploy/nginx.http-only.conf"

  [[ -f "$template" ]] || die "Missing temporary Nginx template: $template"
  sed "s|__APP_DOMAIN__|${DOMAIN}|g" "$template" > "$output"
  log "Rendered temporary HTTP-only Nginx config: $output"
}

validate_dns_points_to_server() {
  local domain_ip server_ip
  domain_ip="$(getent ahosts "$DOMAIN" | awk '/STREAM/ {print $1; exit}')"
  server_ip="$(curl -fsS --max-time 8 https://api.ipify.org || true)"

  [[ -n "$domain_ip" ]] || die "Domain $DOMAIN does not resolve yet. Validate with: nslookup $DOMAIN"
  [[ -n "$server_ip" ]] || warn "Could not determine public server IP automatically"

  if [[ -n "$server_ip" && "$domain_ip" != "$server_ip" ]]; then
    die "DNS mismatch: $DOMAIN -> $domain_ip, but this host public IP is $server_ip"
  fi

  log "DNS check passed for $DOMAIN ($domain_ip)"
}

obtain_certificate() {
  mkdir -p "$PROJECT_DIR/deploy/letsencrypt" "$PROJECT_DIR/deploy/certbot-www"
  chmod 755 "$PROJECT_DIR/deploy/certbot-www"

  if [[ -f "$PROJECT_DIR/deploy/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
    log "Certificate already exists for $DOMAIN; skipping issuance"
    return 0
  fi

  log "Obtaining initial Let's Encrypt certificate for $DOMAIN"
  sudo certbot certonly --standalone \
    --preferred-challenges http \
    --non-interactive \
    --agree-tos \
    --email "$LETSENCRYPT_EMAIL" \
    -d "$DOMAIN" \
    --pre-hook "$PROJECT_DIR/deploy/certbot-hooks/pre-hook.sh" \
    --post-hook "$PROJECT_DIR/deploy/certbot-hooks/post-hook.sh"

  log "Syncing host certs into project bind mount"
  rsync -a /etc/letsencrypt/ "$PROJECT_DIR/deploy/letsencrypt/"
}

install_renewal_timer() {
  local svc_src="$PROJECT_DIR/deploy/systemd/myhealthtracker-cert-renew.service"
  local timer_src="$PROJECT_DIR/deploy/systemd/myhealthtracker-cert-renew.timer"
  local rendered

  rendered="$(mktemp)"
  sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" "$svc_src" > "$rendered"

  sudo cp "$rendered" /etc/systemd/system/myhealthtracker-cert-renew.service
  sudo cp "$timer_src" /etc/systemd/system/
  rm -f "$rendered"

  sudo systemctl daemon-reload
  sudo systemctl enable --now myhealthtracker-cert-renew.timer
  log "Enabled systemd timer for automated cert renewal"
}

run_local_mode() {
  require_cmd curl
  ensure_docker_running
  ensure_compose_v2

  log "Starting local developer stack"
  docker compose up --build -d
  log "Local stack started"
}

run_production_mode() {
  require_cmd curl
  require_cmd rsync
  require_cmd certbot
  ensure_docker_running
  ensure_compose_v2

  load_env_file "$ENV_FILE"
  DOMAIN="${DOMAIN:-}"
  LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL:-}"

  [[ -n "$DOMAIN" ]] || die "DOMAIN must be set in $ENV_FILE"
  [[ -n "$LETSENCRYPT_EMAIL" ]] || die "LETSENCRYPT_EMAIL must be set in $ENV_FILE"

  if [[ "$SKIP_DNS_CHECK" != "true" ]]; then
    validate_dns_points_to_server
  else
    warn "Skipping DNS validation by request"
  fi

  # Validate Compose syntax before mutating runtime state.
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config >/dev/null

  render_http_only_nginx_config
  cp "$PROJECT_DIR/deploy/nginx.http-only.conf" "$PROJECT_DIR/deploy/nginx.conf"

  log "Starting app containers before certificate issuance (without TLS dependency)"
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d db redis backend celery frontend nginx

  obtain_certificate
  render_nginx_config

  log "Reloading Nginx with final TLS configuration"
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d nginx
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T nginx nginx -t
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T nginx nginx -s reload

  install_renewal_timer

  log "Deployment finished successfully"
  log "Validate with: curl -I https://$DOMAIN"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --production) MODE="production" ;;
    --local) MODE="local" ;;
    --env-file) shift; ENV_FILE="${1:-}" ;;
    --skip-dns-check) SKIP_DNS_CHECK="true" ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
  shift
done

if [[ "$MODE" == "local" ]]; then
  run_local_mode
else
  run_production_mode
fi
