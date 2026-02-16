#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

DEPLOY_DIR="$PROJECT_DIR/deploy"
SECRETS_DIR="$DEPLOY_DIR/secrets"
LETSENCRYPT_DIR="$DEPLOY_DIR/letsencrypt"
CERTBOT_WWW_DIR="$DEPLOY_DIR/certbot-www"
NGINX_CONF="$DEPLOY_DIR/nginx.conf"
ENV_FILE="$PROJECT_DIR/.env"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
BACKUP_DIR="$DEPLOY_DIR/backup-$(date +%Y%m%d%H%M%S)"
ROLLBACK_REQUIRED=1

log() { printf "\n[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
warn() { printf "\n[WARN] %s\n" "$*"; }
die() { printf "\n[ERROR] %s\n" "$*"; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

random_secret() {
  openssl rand -base64 48 | tr -d '\n'
}

backup_existing_state() {
  mkdir -p "$BACKUP_DIR"
  [[ -f "$ENV_FILE" ]] && cp "$ENV_FILE" "$BACKUP_DIR/.env.bak"
  [[ -f "$NGINX_CONF" ]] && cp "$NGINX_CONF" "$BACKUP_DIR/nginx.conf.bak"
  [[ -d "$SECRETS_DIR" ]] && cp -R "$SECRETS_DIR" "$BACKUP_DIR/secrets.bak"
}

restore_state() {
  if [[ -f "$BACKUP_DIR/.env.bak" ]]; then cp "$BACKUP_DIR/.env.bak" "$ENV_FILE"; else rm -f "$ENV_FILE"; fi
  if [[ -f "$BACKUP_DIR/nginx.conf.bak" ]]; then cp "$BACKUP_DIR/nginx.conf.bak" "$NGINX_CONF"; else rm -f "$NGINX_CONF"; fi
  if [[ -d "$BACKUP_DIR/secrets.bak" ]]; then rm -rf "$SECRETS_DIR" && cp -R "$BACKUP_DIR/secrets.bak" "$SECRETS_DIR"; else rm -rf "$SECRETS_DIR"; fi
}

rollback() {
  [[ "$ROLLBACK_REQUIRED" -eq 0 ]] && return 0
  warn "Deployment failed. Starting rollback..."
  if [[ -f "$COMPOSE_FILE" ]]; then
    docker compose -f "$COMPOSE_FILE" down --remove-orphans || true
  fi
  restore_state
  warn "Rollback complete. Previous configuration restored."
}

trap rollback ERR

install_packages() {
  if [[ "$EUID" -ne 0 ]]; then
    warn "Root privileges required for package installation and firewall setup. Re-running with sudo."
    exec sudo -E bash "$0"
  fi

  source /etc/os-release
  if [[ "${ID:-}" != "ubuntu" ]]; then
    warn "Detected OS ${PRETTY_NAME:-unknown}. This script is optimized for Ubuntu and may require adjustments."
  fi

  log "Installing required packages..."
  apt-get update
  apt-get install -y ca-certificates curl gnupg lsb-release software-properties-common git nginx certbot ufw

  if ! command -v docker >/dev/null 2>&1; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list >/dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  else
    apt-get install -y docker-compose-plugin
  fi

  systemctl enable --now docker
}

validate_environment() {
  log "Running environment validation checks..."
  require_cmd ss
  require_cmd getent
  require_cmd openssl

  for port in 80 443; do
    if ss -ltn | awk '{print $4}' | grep -Eq ":${port}$"; then
      die "Port ${port} is already in use. Free it before deploying."
    fi
  done

  local mem_kb
  mem_kb="$(awk '/MemAvailable/ {print $2}' /proc/meminfo)"
  if (( mem_kb < 2 * 1024 * 1024 )); then
    die "At least 2GB available memory is required."
  fi

  if ! systemctl is-active --quiet docker; then
    die "Docker service is not active."
  fi

  docker info >/dev/null
}

prompt_inputs() {
  read -rp "Domain name (e.g., app.example.com): " DOMAIN
  [[ -n "$DOMAIN" ]] || die "Domain is required."

  local resolved
  resolved="$(getent ahosts "$DOMAIN" | awk '/STREAM/ {print $1; exit}')"
  [[ -n "$resolved" ]] || die "Domain $DOMAIN does not resolve yet."

  local public_ip
  public_ip="$(curl -s --max-time 5 https://api.ipify.org || true)"
  if [[ -n "$public_ip" && "$public_ip" != "$resolved" ]]; then
    warn "DNS resolves to $resolved but this server appears as $public_ip. SSL provisioning may fail."
  fi

  read -rsp "OpenAI API key: " OPENAI_API_KEY; echo
  read -rp "JWT secret (leave blank to auto-generate): " JWT_SECRET
  [[ -n "$JWT_SECRET" ]] || JWT_SECRET="$(random_secret)"
  read -rp "Email for SSL notifications: " SSL_EMAIL
  [[ -n "$SSL_EMAIL" ]] || die "SSL email is required."

  read -rp "Enable Apple Health sync? (Y/N): " APPLE_HEALTH_SYNC
  APPLE_HEALTH_SYNC="$(echo "$APPLE_HEALTH_SYNC" | tr '[:lower:]' '[:upper:]')"
  [[ "$APPLE_HEALTH_SYNC" =~ ^(Y|N)$ ]] || die "Apple Health sync must be Y or N."

  read -rp "Enable WhatsApp integration? (Y/N): " WHATSAPP_ENABLED
  WHATSAPP_ENABLED="$(echo "$WHATSAPP_ENABLED" | tr '[:lower:]' '[:upper:]')"
  [[ "$WHATSAPP_ENABLED" =~ ^(Y|N)$ ]] || die "WhatsApp integration must be Y or N."
}

generate_configuration() {
  log "Generating secrets and environment files..."
  mkdir -p "$SECRETS_DIR" "$LETSENCRYPT_DIR" "$CERTBOT_WWW_DIR"
  chmod 700 "$SECRETS_DIR"

  DB_PASSWORD="$(random_secret)"
  REDIS_PASSWORD="$(random_secret)"
  ADMIN_PASSWORD="$(random_secret)"

  printf "%s" "$DB_PASSWORD" > "$SECRETS_DIR/db_password"
  printf "%s" "$REDIS_PASSWORD" > "$SECRETS_DIR/redis_password"
  chmod 600 "$SECRETS_DIR"/*

  cat > "$ENV_FILE" <<ENVVARS
ENVIRONMENT=production
DOMAIN=${DOMAIN}
POSTGRES_DB=metabolic
POSTGRES_USER=metabolic
DATABASE_URL=postgresql+psycopg2://metabolic:${DB_PASSWORD}@db:5432/metabolic
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/0
OPENAI_API_KEY=${OPENAI_API_KEY}
OPENAI_MODEL=gpt-4o-mini
JWT_SECRET=${JWT_SECRET}
SSL_EMAIL=${SSL_EMAIL}
APPLE_HEALTH_SYNC_ENABLED=$([[ "$APPLE_HEALTH_SYNC" == "Y" ]] && echo "true" || echo "false")
WHATSAPP_ENABLED=$([[ "$WHATSAPP_ENABLED" == "Y" ]] && echo "true" || echo "false")
NEXT_PUBLIC_API_BASE_URL=https://${DOMAIN}/api
ADMIN_DEFAULT_USER=admin
ADMIN_DEFAULT_PASSWORD=${ADMIN_PASSWORD}
ENVVARS

  cat > "$NGINX_CONF" <<NGINX
upstream backend_upstream {
    server backend:8000;
}

upstream frontend_upstream {
    server frontend:3000;
}

server {
    listen 80;
    server_name ${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN};

    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 20m;

    location /api/ {
        proxy_pass http://backend_upstream/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location / {
        proxy_pass http://frontend_upstream;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX
}

configure_ssl() {
  log "Provisioning Let's Encrypt certificates..."
  certbot certonly --standalone --non-interactive --agree-tos --email "$SSL_EMAIL" -d "$DOMAIN"
  mkdir -p "$LETSENCRYPT_DIR/live/$DOMAIN"
  cp -Lr "/etc/letsencrypt/live/$DOMAIN" "$LETSENCRYPT_DIR/live/"
  cp -Lr /etc/letsencrypt/archive "$LETSENCRYPT_DIR/" || true
  cp -L /etc/letsencrypt/options-ssl-nginx.conf "$LETSENCRYPT_DIR/options-ssl-nginx.conf" || true
  cp -L /etc/letsencrypt/ssl-dhparams.pem "$LETSENCRYPT_DIR/ssl-dhparams.pem" || true
}

configure_firewall() {
  log "Configuring firewall..."
  ufw --force reset
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow OpenSSH
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw --force enable
}

start_stack() {
  log "Starting production stack..."
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
}

verify_stack() {
  log "Verifying deployed services..."
  docker compose -f "$COMPOSE_FILE" ps

  curl -fsS "https://${DOMAIN}/api/health" >/dev/null
  curl -fsS "https://${DOMAIN}" >/dev/null

  docker compose -f "$COMPOSE_FILE" exec -T db psql -U metabolic -d metabolic -c "SELECT 1;" >/dev/null
}

print_summary() {
  cat <<SUMMARY

Deployment completed successfully.

App URL: https://${DOMAIN}
API URL: https://${DOMAIN}/api
Admin login:
  Username: admin
  Password: ${ADMIN_PASSWORD}

Next steps:
  1. Store secrets securely (password manager / vault).
  2. Set up automated backups for postgres_data volume.
  3. Add monitoring/alerting (Prometheus + Grafana or hosted APM).
  4. Rotate OpenAI and JWT secrets periodically.
  5. Configure a certbot renewal cron job and copy renewed certs into deploy/letsencrypt.
SUMMARY
}

main() {
  backup_existing_state
  install_packages
  validate_environment
  prompt_inputs
  generate_configuration
  configure_ssl
  configure_firewall
  start_stack
  verify_stack
  ROLLBACK_REQUIRED=0
  print_summary
}

main "$@"
