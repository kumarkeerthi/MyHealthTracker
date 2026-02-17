#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
DEPLOY_LOG="${LOG_DIR}/deploy.log"
SECRETS_FILE="${PROJECT_DIR}/generated_secrets.env"
MODE="local"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"
ENV_FILE="${PROJECT_DIR}/.env.local"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$DEPLOY_LOG") 2>&1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prod)
      MODE="production"
      COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
      ENV_FILE="${PROJECT_DIR}/.env.production"
      ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
  shift
done

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die() { printf '[ERROR] %s\n' "$*" >&2; exit 1; }

[[ -f "$SECRETS_FILE" ]] || die "Missing generated_secrets.env"
[[ -f "$ENV_FILE" ]] || die "Missing env file: $ENV_FILE"

log "Validating environment"
"${PROJECT_DIR}/validate_env.sh" $([[ "$MODE" == "production" ]] && echo "--prod")

set -a
# shellcheck disable=SC1090
source "$SECRETS_FILE"
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ "$MODE" == "production" ]]; then
  [[ -f "${PROJECT_DIR}/nginx.conf.template" ]] || die "Missing nginx.conf.template"
  sed "s|__APP_DOMAIN__|${APP_DOMAIN}|g" "${PROJECT_DIR}/nginx.conf.template" > "${PROJECT_DIR}/deploy/nginx.conf"
fi

ensure_admin_credentials() {
  if grep -q '^ADMIN_EMAIL=' "$SECRETS_FILE" && grep -q '^ADMIN_PASSWORD=' "$SECRETS_FILE" && grep -q '^ADMIN_PASSWORD_HASH=' "$SECRETS_FILE"; then
    ADMIN_EMAIL="$(awk -F= '/^ADMIN_EMAIL=/{print $2}' "$SECRETS_FILE" | tail -1)"
    ADMIN_PASSWORD="$(awk -F= '/^ADMIN_PASSWORD=/{print $2}' "$SECRETS_FILE" | tail -1)"
    ADMIN_PASSWORD_HASH="$(awk -F= '/^ADMIN_PASSWORD_HASH=/{print substr($0,index($0,"=")+1)}' "$SECRETS_FILE" | tail -1)"
    return
  fi

  ADMIN_EMAIL="admin@local"
  ADMIN_PASSWORD="$(openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 16)"
  ADMIN_PASSWORD_HASH="$(python3 - <<'PY' "$ADMIN_PASSWORD"
import bcrypt, sys
print(bcrypt.hashpw(sys.argv[1].encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))
PY
)"

  tmp="$(mktemp)"
  awk -F= '!/^ADMIN_EMAIL=|^ADMIN_PASSWORD=|^ADMIN_PASSWORD_HASH=/' "$SECRETS_FILE" > "$tmp"
  {
    echo "ADMIN_EMAIL=${ADMIN_EMAIL}"
    echo "ADMIN_PASSWORD=${ADMIN_PASSWORD}"
    echo "ADMIN_PASSWORD_HASH=${ADMIN_PASSWORD_HASH}"
  } >> "$tmp"
  mv "$tmp" "$SECRETS_FILE"
  chmod 600 "$SECRETS_FILE"
}

ensure_admin_credentials
export ADMIN_EMAIL ADMIN_PASSWORD ADMIN_PASSWORD_HASH

log "Building images"
docker compose -f "$COMPOSE_FILE" --env-file "$SECRETS_FILE" --env-file "$ENV_FILE" build

log "Starting data services"
docker compose -f "$COMPOSE_FILE" --env-file "$SECRETS_FILE" --env-file "$ENV_FILE" up -d db redis

docker compose -f "$COMPOSE_FILE" --env-file "$SECRETS_FILE" --env-file "$ENV_FILE" exec -T db sh -c 'until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do sleep 2; done'

log "Running migrations"
docker compose -f "$COMPOSE_FILE" --env-file "$SECRETS_FILE" --env-file "$ENV_FILE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE TABLE IF NOT EXISTS schema_migrations (filename text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());" >/dev/null
for migration in "${PROJECT_DIR}"/migrations/*.sql; do
  fname="$(basename "$migration")"
  if docker compose -f "$COMPOSE_FILE" --env-file "$SECRETS_FILE" --env-file "$ENV_FILE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM schema_migrations WHERE filename='${fname}'" | grep -q 1; then
    continue
  fi
  cat "$migration" | docker compose -f "$COMPOSE_FILE" --env-file "$SECRETS_FILE" --env-file "$ENV_FILE" exec -T db psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"
  docker compose -f "$COMPOSE_FILE" --env-file "$SECRETS_FILE" --env-file "$ENV_FILE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "INSERT INTO schema_migrations(filename) VALUES ('${fname}') ON CONFLICT DO NOTHING;" >/dev/null
done

log "Starting app services"
docker compose -f "$COMPOSE_FILE" --env-file "$SECRETS_FILE" --env-file "$ENV_FILE" up -d

log "Seeding admin user"
docker compose -f "$COMPOSE_FILE" --env-file "$SECRETS_FILE" --env-file "$ENV_FILE" exec -T backend python - <<'PY'
import os
from app.db.session import SessionLocal
from app.models.models import User

email = os.environ['ADMIN_EMAIL']
hashed = os.environ['ADMIN_PASSWORD_HASH']

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == email).one_or_none()
    if user:
        user.hashed_password = hashed
        user.role = 'admin'
    else:
        db.add(User(
            email=email,
            hashed_password=hashed,
            role='admin',
            age=30,
            sex='unspecified',
            triglycerides=120,
            hdl=50,
            hba1c=5.6,
            insulin_resistant=True,
            diet_type='omnivore',
        ))
    db.commit()
finally:
    db.close()
PY

cat <<MSG
--------------------------------------------
Metabolic OS Setup Complete
--------------------------------------------
Mode: ${MODE^^}
URL: $([[ "$MODE" == "production" ]] && echo "https://${APP_DOMAIN}" || echo "http://localhost:3000")

Admin Login:
Email: ${ADMIN_EMAIL}
Password: ${ADMIN_PASSWORD}

Secrets saved in:
${SECRETS_FILE}
--------------------------------------------
MSG
