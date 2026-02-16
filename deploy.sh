#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${PROJECT_DIR}/deploy/lib.sh"

COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
BACKUP_ROOT="${PROJECT_DIR}/deploy/backups"
RUN_BACKUP_DIR="${BACKUP_ROOT}/$(date +%Y%m%d_%H%M%S)"
ROLLBACK_NEEDED=1

exec > >(tee -a "$DEPLOY_LOG") 2>&1

backup_current_state() {
  mkdir -p "$RUN_BACKUP_DIR"
  [[ -f "$ENV_FILE" ]] && cp "$ENV_FILE" "$RUN_BACKUP_DIR/.env"
  [[ -f "$NGINX_RENDERED_CONF" ]] && cp "$NGINX_RENDERED_CONF" "$RUN_BACKUP_DIR/nginx.conf"
  [[ -d "${PROJECT_DIR}/deploy/letsencrypt" ]] && cp -a "${PROJECT_DIR}/deploy/letsencrypt" "$RUN_BACKUP_DIR/letsencrypt"
  docker compose -f "$COMPOSE_FILE" ps --format json > "$RUN_BACKUP_DIR/compose_state.json" || true
}

restore_previous_state() {
  if [[ -f "$RUN_BACKUP_DIR/.env" ]]; then cp "$RUN_BACKUP_DIR/.env" "$ENV_FILE"; fi
  if [[ -f "$RUN_BACKUP_DIR/nginx.conf" ]]; then cp "$RUN_BACKUP_DIR/nginx.conf" "$NGINX_RENDERED_CONF"; fi
  if [[ -d "$RUN_BACKUP_DIR/letsencrypt" ]]; then
    rm -rf "${PROJECT_DIR}/deploy/letsencrypt"
    cp -a "$RUN_BACKUP_DIR/letsencrypt" "${PROJECT_DIR}/deploy/letsencrypt"
  fi
}

rollback() {
  [[ "$ROLLBACK_NEEDED" -eq 1 ]] || return 0
  warn "Deployment failed. Initiating rollback..."
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --remove-orphans || true
  restore_previous_state
  if [[ -f "$RUN_BACKUP_DIR/.env" ]]; then
    warn "Attempting to restore prior stack..."
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d || true
  fi
  warn "Rollback complete. Check ${DEPLOY_LOG} for details."
}

trap rollback ERR

load_and_validate_env() {
  [[ -f "$ENV_FILE" ]] || die "Missing .env. Run ./bootstrap.sh first."
  # shellcheck disable=SC1090
  source "$ENV_FILE"

  validate_required_env APP_DOMAIN POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD OPENAI_API_KEY CORS_ALLOWED_ORIGINS NEXT_PUBLIC_API_BASE_URL JWT_SECRET REDIS_PASSWORD ADMIN_EMAIL ADMIN_PASSWORD_HASH
  validate_openai_key
  validate_domain_points_here "$APP_DOMAIN"
  validate_docker_running
}

prepare_runtime_directories() {
  mkdir -p /data/postgres /data/uploads /backups /logs \
    "${PROJECT_DIR}/deploy/letsencrypt" "${PROJECT_DIR}/deploy/certbot-www"
}

create_postgres_volume() {
  log "Ensuring postgres volume exists"
  docker volume create myhealthtracker_postgres_data >/dev/null
}

build_containers() {
  log "Building images"
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build
}

start_data_services() {
  log "Starting postgres and redis"
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d db redis
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db sh -c 'until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do sleep 2; done'
}

run_migrations() {
  log "Applying SQL migrations"
  local migration
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE TABLE IF NOT EXISTS schema_migrations (filename text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());" >/dev/null
  for migration in "${PROJECT_DIR}"/migrations/*.sql; do
    [[ -f "$migration" ]] || continue
    local fname
    fname="$(basename "$migration")"
    if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM schema_migrations WHERE filename='${fname}'" | grep -q 1; then
      log "Migration already applied: ${fname}"
      continue
    fi
    cat "$migration" | docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "INSERT INTO schema_migrations(filename) VALUES ('${fname}') ON CONFLICT DO NOTHING;" >/dev/null
  done
}

seed_admin_user() {
  log "Seeding admin user"
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d backend
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T backend python - <<'PY'
import os
from app.db.session import SessionLocal
from app.models.models import User

email = os.environ["ADMIN_EMAIL"]
hashed = os.environ["ADMIN_PASSWORD_HASH"]

db = SessionLocal()
try:
    existing = db.query(User).filter(User.email == email).one_or_none()
    if existing:
        existing.hashed_password = hashed
        existing.role = "admin"
    else:
        db.add(User(
            email=email,
            hashed_password=hashed,
            role="admin",
            age=30,
            sex="unspecified",
            triglycerides=120,
            hdl=50,
            hba1c=5.6,
            insulin_resistant=True,
            diet_type="omnivore",
        ))
    db.commit()
finally:
    db.close()
PY
}

configure_nginx_and_ssl() {
  log "Rendering Nginx config"
  render_nginx_config "$APP_DOMAIN"

  log "Bringing up full stack"
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d frontend backend celery nginx container-watchdog

  log "Requesting SSL certificate"
  docker run --rm \
    -p 80:80 \
    -v "${PROJECT_DIR}/deploy/letsencrypt:/etc/letsencrypt" \
    -v "${PROJECT_DIR}/deploy/certbot-www:/var/www/certbot" \
    certbot/certbot certonly --standalone --non-interactive --agree-tos \
    --register-unsafely-without-email -d "$APP_DOMAIN" || warn "Certbot failed. Ensure DNS and port 80 are publicly reachable."

  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart nginx
}

configure_firewall() {
  log "Configuring UFW firewall"
  ufw --force reset
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw --force enable
}

verify_health() {
  log "Verifying health endpoint"
  curl -fsS "https://${APP_DOMAIN}/health" >/dev/null || curl -fsS "http://localhost:8000/health" >/dev/null
}

print_success() {
  cat <<MSG
--------------------------------------------
Metabolic OS successfully deployed!
--------------------------------------------
URL: https://${APP_DOMAIN}
Admin login: ${ADMIN_EMAIL}
Next Steps:
1. Login
2. Complete onboarding
3. Enable push notifications
MSG
}

main() {
  ensure_logs_dir
  ensure_root_or_sudo "$@"
  log "Starting deployment. Logs: ${DEPLOY_LOG}"

  require_cmd docker
  require_cmd ufw
  require_cmd curl

  backup_current_state
  load_and_validate_env
  prepare_runtime_directories
  create_postgres_volume
  build_containers
  start_data_services
  run_migrations
  seed_admin_user
  configure_nginx_and_ssl
  configure_firewall
  verify_health

  ROLLBACK_NEEDED=0
  print_success
}

main "$@"
