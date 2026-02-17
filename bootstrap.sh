#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
BOOTSTRAP_LOG="${LOG_DIR}/bootstrap.log"
SECRETS_FILE="${PROJECT_DIR}/generated_secrets.env"
LOCAL_ENV_FILE="${PROJECT_DIR}/.env.local"
PROD_ENV_FILE="${PROJECT_DIR}/.env.production"
REGEN_SECRETS=0

mkdir -p "$LOG_DIR"
exec > >(tee -a "$BOOTSTRAP_LOG") 2>&1

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die() { printf '[ERROR] %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --regen)
      REGEN_SECRETS=1
      ;;
    -h|--help)
      printf '%s\n' 'Usage: ./bootstrap.sh [--regen]'
      exit 0
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
  shift
done

command_exists() { command -v "$1" >/dev/null 2>&1; }

ensure_package() {
  local cmd="$1"
  local pkg="$2"
  if command_exists "$cmd"; then
    return 0
  fi
  if command_exists apt-get; then
    log "Installing missing dependency: ${pkg}"
    apt-get update -y >/dev/null
    DEBIAN_FRONTEND=noninteractive apt-get install -y "$pkg" >/dev/null
  fi
  command_exists "$cmd" || die "Missing dependency: ${cmd}"
}

install_dependencies() {
  ensure_package openssl openssl
  ensure_package docker docker.io
  if ! docker compose version >/dev/null 2>&1; then
    if command_exists apt-get; then
      log "Installing docker compose plugin"
      DEBIAN_FRONTEND=noninteractive apt-get install -y docker-compose-plugin >/dev/null
    fi
    docker compose version >/dev/null 2>&1 || die 'Docker Compose plugin is required'
  fi
}

read_env_value() {
  local file="$1"
  local key="$2"
  local line
  if [[ ! -f "$file" ]]; then
    return 1
  fi
  line="$(awk -F= -v k="$key" '$1==k {print substr($0, index($0, "=")+1)}' "$file" | tail -n 1)"
  if [[ -z "$line" ]]; then
    return 1
  fi
  printf '%s' "$line"
}

validate_openai_key() {
  local key="$1"
  [[ "$key" == sk-* && ${#key} -ge 40 ]]
}

prompt_openai_key() {
  local key
  while true; do
    printf '%s\n' '--------------------------------------------' >&2
    printf '%s\n' 'Enter your OpenAI API key (starts with sk-)' >&2
    printf '%s\n' '--------------------------------------------' >&2
    read -rsp 'OPENAI_API_KEY: ' key
    printf '\n' >&2
    if validate_openai_key "$key"; then
      printf '%s' "$key"
      return 0
    fi
    printf '%s\n' '[WARN] Invalid key. Try again.' >&2
  done
}

random_hex_32() {
  openssl rand -hex 32
}

write_secrets_file() {
  local openai_key="$1"
  local admin_password="$2"
  local tmp
  tmp="$(mktemp)"
  printf 'POSTGRES_USER=%s\n' 'metabolic_user' > "$tmp"
  printf 'POSTGRES_PASSWORD=%s\n' "$(random_hex_32)" >> "$tmp"
  printf 'POSTGRES_DB=%s\n' 'metabolic_db' >> "$tmp"
  printf 'REDIS_PASSWORD=%s\n' "$(random_hex_32)" >> "$tmp"
  printf 'JWT_SECRET=%s\n' "$(random_hex_32)" >> "$tmp"
  printf 'INTERNAL_API_KEY=%s\n' "$(random_hex_32)" >> "$tmp"
  printf 'SESSION_SECRET=%s\n' "$(random_hex_32)" >> "$tmp"
  printf 'VAPID_PUBLIC_KEY=%s\n' "$(random_hex_32)" >> "$tmp"
  printf 'VAPID_PRIVATE_KEY=%s\n' "$(random_hex_32)" >> "$tmp"
  printf 'OPENAI_API_KEY=%s\n' "$openai_key" >> "$tmp"
  printf 'ADMIN_EMAIL=%s\n' 'admin@local' >> "$tmp"
  printf 'ADMIN_PASSWORD=%s\n' "$admin_password" >> "$tmp"
  mv "$tmp" "$SECRETS_FILE"
  chmod 600 "$SECRETS_FILE"
}

write_env_file() {
  local target_file="$1"
  local mode="$2"
  local app_domain="$3"
  local next_public_api_base_url="$4"
  local cors_allowed_origins="$5"
  local food_public_base="$6"
  local require_https="$7"
  local tmp
  tmp="$(mktemp)"

  printf 'ENVIRONMENT=%s\n' "$mode" > "$tmp"
  printf 'APP_DOMAIN=%s\n' "$app_domain" >> "$tmp"
  printf 'OPENAI_API_KEY=%s\n' "$OPENAI_API_KEY" >> "$tmp"
  printf 'OPENAI_MODEL=%s\n' 'gpt-4o-mini' >> "$tmp"
  printf 'CORS_ALLOWED_ORIGINS=%s\n' "$cors_allowed_origins" >> "$tmp"
  printf 'NEXT_PUBLIC_API_BASE_URL=%s\n' "$next_public_api_base_url" >> "$tmp"
  printf 'REQUIRE_HTTPS=%s\n' "$require_https" >> "$tmp"
  printf 'POSTGRES_USER=%s\n' "$POSTGRES_USER" >> "$tmp"
  printf 'POSTGRES_PASSWORD=%s\n' "$POSTGRES_PASSWORD" >> "$tmp"
  printf 'POSTGRES_DB=%s\n' "$POSTGRES_DB" >> "$tmp"
  printf 'DATABASE_URL=%s\n' "postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}" >> "$tmp"
  printf 'REDIS_PASSWORD=%s\n' "$REDIS_PASSWORD" >> "$tmp"
  printf 'REDIS_URL=%s\n' "redis://:${REDIS_PASSWORD}@redis:6379/0" >> "$tmp"
  printf 'CELERY_BROKER_URL=%s\n' "redis://:${REDIS_PASSWORD}@redis:6379/0" >> "$tmp"
  printf 'CELERY_RESULT_BACKEND=%s\n' "redis://:${REDIS_PASSWORD}@redis:6379/0" >> "$tmp"
  printf 'JWT_SECRET=%s\n' "$JWT_SECRET" >> "$tmp"
  printf 'INTERNAL_API_KEY=%s\n' "$INTERNAL_API_KEY" >> "$tmp"
  printf 'SESSION_SECRET=%s\n' "$SESSION_SECRET" >> "$tmp"
  printf 'VAPID_PUBLIC_KEY=%s\n' "$VAPID_PUBLIC_KEY" >> "$tmp"
  printf 'VAPID_PRIVATE_KEY=%s\n' "$VAPID_PRIVATE_KEY" >> "$tmp"
  printf 'VAPID_SUBJECT=%s\n' 'mailto:admin@local' >> "$tmp"
  printf 'ADMIN_EMAIL=%s\n' "$ADMIN_EMAIL" >> "$tmp"
  printf 'ADMIN_PASSWORD=%s\n' "$ADMIN_PASSWORD" >> "$tmp"
  printf 'LOG_LEVEL=%s\n' 'INFO' >> "$tmp"
  printf 'LOG_DIR=%s\n' '/logs' >> "$tmp"
  printf 'FOOD_IMAGE_UPLOAD_DIR=%s\n' '/data/uploads' >> "$tmp"
  printf 'FOOD_IMAGE_PUBLIC_BASE_URL=%s\n' "$food_public_base" >> "$tmp"

  mv "$tmp" "$target_file"
  chmod 600 "$target_file"
}

load_required_from_secrets() {
  local key
  for key in POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB REDIS_PASSWORD JWT_SECRET INTERNAL_API_KEY SESSION_SECRET VAPID_PUBLIC_KEY VAPID_PRIVATE_KEY OPENAI_API_KEY ADMIN_EMAIL ADMIN_PASSWORD; do
    value="$(read_env_value "$SECRETS_FILE" "$key")"
    printf -v "$key" '%s' "$value"
    export "$key"
  done
}

main() {
  local openai_key
  local admin_password
  local app_domain

  install_dependencies

  if [[ -f "$SECRETS_FILE" && "$REGEN_SECRETS" -eq 0 ]]; then
    log 'Reusing existing generated_secrets.env (pass --regen to regenerate).'
  else
    openai_key=""
    if [[ -f "$SECRETS_FILE" ]]; then
      openai_key="$(read_env_value "$SECRETS_FILE" 'OPENAI_API_KEY' || true)"
    fi
    if ! validate_openai_key "$openai_key"; then
      openai_key="$(prompt_openai_key)"
    fi

    admin_password="$(random_hex_32)"
    write_secrets_file "$openai_key" "$admin_password"
    log 'Wrote generated_secrets.env'
  fi

  load_required_from_secrets

  app_domain='localhost'
  if [[ -f "$PROD_ENV_FILE" ]]; then
    existing_domain="$(read_env_value "$PROD_ENV_FILE" 'APP_DOMAIN' || true)"
    if [[ -n "$existing_domain" ]]; then
      app_domain="$existing_domain"
    fi
  fi

  write_env_file "$PROD_ENV_FILE" 'production' "$app_domain" "https://${app_domain}/api" "https://${app_domain}" "https://${app_domain}/uploads" 'true'
  write_env_file "$LOCAL_ENV_FILE" 'local' 'localhost' 'http://localhost:8000' 'http://localhost:3000' 'http://localhost:8000/uploads' 'false'

  log 'Wrote .env.production and .env.local'
  log 'Bootstrap complete. Next: ./deploy.sh'
}

main "$@"
