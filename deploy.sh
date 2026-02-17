#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
DEPLOY_LOG="${LOG_DIR}/deploy.log"
ENV_PROD_FILE="${PROJECT_DIR}/.env.production"
ENV_LOCAL_FILE="${PROJECT_DIR}/.env.local"
SECRETS_FILE="${PROJECT_DIR}/generated_secrets.env"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$DEPLOY_LOG") 2>&1

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die() { printf '[ERROR] %s\n' "$*" >&2; exit 1; }

[[ -f "$SECRETS_FILE" ]] || die 'Missing generated_secrets.env. Run ./bootstrap.sh first.'
[[ -f "$ENV_PROD_FILE" ]] || die 'Missing .env.production. Run ./bootstrap.sh first.'
[[ -f "$ENV_LOCAL_FILE" ]] || die 'Missing .env.local. Run ./bootstrap.sh first.'

load_env_file() {
  local file="$1"
  local line
  local key
  local value
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" ]] && continue
    [[ "$line" == \#* ]] && continue
    key="${line%%=*}"
    value="${line#*=}"
    [[ -n "$key" ]] || continue
    printf -v "$key" '%s' "$value"
    export "$key"
  done < "$file"
}

validate_env_file_format() {
  local file="$1"
  local name
  name="$(basename "$file")"

  if grep -nE '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=.*\$\{' "$file" >/dev/null; then
    die "${name} contains forbidden interpolation syntax"
  fi

  if grep -nE '^[A-Za-z_][A-Za-z0-9_]*=$' "$file" >/dev/null; then
    die "${name} contains empty variables"
  fi

  if grep -nE '^[A-Za-z_][A-Za-z0-9_]*=.*[[:space:]]+$' "$file" >/dev/null; then
    die "${name} contains trailing spaces"
  fi
}

log 'Running pre-deploy validation'
validate_env_file_format "$SECRETS_FILE"
validate_env_file_format "$ENV_PROD_FILE"
validate_env_file_format "$ENV_LOCAL_FILE"

load_env_file "$ENV_PROD_FILE"

required_vars=(
  POSTGRES_USER
  POSTGRES_PASSWORD
  POSTGRES_DB
  REDIS_PASSWORD
  JWT_SECRET
  INTERNAL_API_KEY
  SESSION_SECRET
  VAPID_PUBLIC_KEY
  VAPID_PRIVATE_KEY
  OPENAI_API_KEY
  ADMIN_EMAIL
  ADMIN_PASSWORD
)

for key in "${required_vars[@]}"; do
  value="${!key}"
  if [[ -z "$value" ]]; then
    die "Required variable is empty: ${key}"
  fi
  if [[ "$value" == *'{'* ]]; then
    die "Variable ${key} contains forbidden brace characters"
  fi
  if [[ "$value" == *'}'* ]]; then
    die "Variable ${key} contains forbidden brace characters"
  fi
done

if [[ "$POSTGRES_USER" == *'${POSTGRES_USER}'* ]]; then
  die 'POSTGRES_USER is a literal placeholder value'
fi

if [[ "$OPENAI_API_KEY" != sk-* ]]; then
  die 'OPENAI_API_KEY must start with sk-'
fi

if [[ ${#OPENAI_API_KEY} -lt 40 ]]; then
  die 'OPENAI_API_KEY is too short'
fi

log 'Validation passed'

if ! docker info >/dev/null 2>&1; then
  die 'Docker daemon is not running'
fi

log 'Building images'
docker compose -f "$COMPOSE_FILE" build

log 'Starting core services'
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans db redis

log 'Waiting for PostgreSQL readiness'
until docker compose -f "$COMPOSE_FILE" exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; do
  sleep 2
done

log 'Running migrations'
docker compose -f "$COMPOSE_FILE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'CREATE TABLE IF NOT EXISTS schema_migrations (filename text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());' >/dev/null
for migration in "${PROJECT_DIR}"/migrations/*.sql; do
  fname="$(basename "$migration")"
  if docker compose -f "$COMPOSE_FILE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM schema_migrations WHERE filename='${fname}'" | grep -q 1; then
    continue
  fi
  cat "$migration" | docker compose -f "$COMPOSE_FILE" exec -T db psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"
  docker compose -f "$COMPOSE_FILE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "INSERT INTO schema_migrations(filename) VALUES ('${fname}') ON CONFLICT DO NOTHING;" >/dev/null
done

log 'Bootstrapping base schema'
docker compose -f "$COMPOSE_FILE" run --rm backend python - <<'PY'
from app.db.base import Base
from app.db.session import engine
import app.models.models  # noqa: F401

Base.metadata.create_all(bind=engine)
PY

log 'Starting full stack'
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

log 'Seeding admin user'
docker compose -f "$COMPOSE_FILE" exec -T backend python - <<'PY'
import os
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.models import User

email = os.environ['ADMIN_EMAIL']
password = os.environ['ADMIN_PASSWORD']
hashed = hash_password(password)

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

printf '%s\n' '--------------------------------------------'
printf '%s\n' 'Metabolic OS Setup Complete'
printf '%s\n' '--------------------------------------------'
printf 'URL: %s\n' 'http://localhost:3000'
printf '%s\n' ''
printf '%s\n' 'Admin Login:'
printf 'Email: %s\n' "$ADMIN_EMAIL"
printf 'Password: %s\n' "$ADMIN_PASSWORD"
printf '%s\n' '--------------------------------------------'
