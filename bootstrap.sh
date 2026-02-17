#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
BOOTSTRAP_LOG="${LOG_DIR}/bootstrap.log"
SECRETS_FILE="${PROJECT_DIR}/generated_secrets.env"
REFERENCE_FILE="${PROJECT_DIR}/setup_reference.env"
LOCAL_TEMPLATE="${PROJECT_DIR}/.env.local.template"
PROD_TEMPLATE="${PROJECT_DIR}/.env.production.template"
MODE="local"
FORCE=0
REGEN_SECRETS=0

mkdir -p "$LOG_DIR"
exec > >(tee -a "$BOOTSTRAP_LOG") 2>&1

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
warn() { printf '[WARN] %s\n' "$*"; }
die() { printf '[ERROR] %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<USAGE
Usage: ./bootstrap.sh [--prod] [--force] [--regen-secrets]
  --prod            Generate production env (.env.production)
  --force           Overwrite existing target env file
  --regen-secrets   Regenerate generated_secrets.env
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prod) MODE="production" ;;
    --force) FORCE=1 ;;
    --regen-secrets) REGEN_SECRETS=1 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
  shift
done

command_exists() { command -v "$1" >/dev/null 2>&1; }

ensure_package() {
  local cmd="$1" pkg="$2"
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
  ensure_package curl curl
  ensure_package openssl openssl
  ensure_package docker docker.io

  if ! docker compose version >/dev/null 2>&1; then
    if command_exists apt-get; then
      log "Installing docker compose plugin"
      DEBIAN_FRONTEND=noninteractive apt-get install -y docker-compose-plugin >/dev/null
    fi
    docker compose version >/dev/null 2>&1 || die "Docker Compose plugin is required"
  fi

  if [[ "$MODE" == "production" ]]; then
    ensure_package nginx nginx
  fi
}

random_hex_32() {
  openssl rand -hex 32
}

upsert_secret() {
  local key="$1" value="$2"
  local tmp
  tmp="$(mktemp)"
  if [[ -f "$SECRETS_FILE" ]]; then
    awk -F= -v k="$key" '$1!=k {print}' "$SECRETS_FILE" > "$tmp"
  fi
  printf '%s=%s\n' "$key" "$value" >> "$tmp"
  mv "$tmp" "$SECRETS_FILE"
}

generate_secrets_file() {
  if [[ -f "$SECRETS_FILE" && "$REGEN_SECRETS" -eq 0 ]]; then
    log "Reusing existing generated secrets: ${SECRETS_FILE}"
    return
  fi

  log "Generating deterministic secret file: ${SECRETS_FILE}"
  cat > "$SECRETS_FILE" <<EOF_SECRETS
POSTGRES_USER=metabolic_user
POSTGRES_PASSWORD=$(random_hex_32)
POSTGRES_DB=metabolic_db
REDIS_PASSWORD=$(random_hex_32)
JWT_SECRET=$(random_hex_32)
INTERNAL_API_KEY=$(random_hex_32)
SESSION_SECRET=$(random_hex_32)
VAPID_PUBLIC_KEY=$(random_hex_32)
VAPID_PRIVATE_KEY=$(random_hex_32)
EOF_SECRETS
  chmod 600 "$SECRETS_FILE"
}

prompt_openai_key() {
  local key
  while true; do
    cat <<'MSG' >&2
--------------------------------------------
To retrieve OpenAI API Key:
1. Visit https://platform.openai.com
2. Click "API Keys"
3. Create new secret key
4. Paste it here
--------------------------------------------
MSG
    read -rsp "OPENAI_API_KEY: " key
    echo >&2
    if [[ "$key" == sk-* && ${#key} -ge 40 ]]; then
      printf '%s' "$key"
      return 0
    fi
    warn "Invalid key. It must start with 'sk-' and be at least 40 characters." >&2
  done
}

resolve_openai_key() {
  if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    if [[ "$OPENAI_API_KEY" == sk-* && ${#OPENAI_API_KEY} -ge 40 ]]; then
      printf '%s' "$OPENAI_API_KEY"
      return 0
    fi
    die "OPENAI_API_KEY was provided but is invalid"
  fi

  prompt_openai_key
}

render_env_file() {
  local target_file template_file openai_key app_domain
  if [[ "$MODE" == "production" ]]; then
    target_file="${PROJECT_DIR}/.env.production"
    template_file="$PROD_TEMPLATE"
  else
    target_file="${PROJECT_DIR}/.env.local"
    template_file="$LOCAL_TEMPLATE"
  fi

  [[ -f "$template_file" ]] || die "Missing template: $template_file"

  if [[ -f "$target_file" && "$FORCE" -eq 0 ]]; then
    log "Skipping existing ${target_file} (use --force to overwrite)"
    return 0
  fi

  openai_key="$(resolve_openai_key)"
  app_domain="${APP_DOMAIN:-localhost}"

  # Load generated deterministic secrets so template variables expand to concrete values.
  set -a
  # shellcheck disable=SC1090
  source "$SECRETS_FILE"
  set +a

  local tmp
  tmp="$(mktemp)"
  OPENAI_API_KEY="$openai_key" APP_DOMAIN="$app_domain" envsubst < "$template_file" > "$tmp"
  [[ -s "$tmp" ]] || die "Generated env file is empty"
  if rg -n 'CHANGEME|=$|\$\{[A-Za-z_][A-Za-z0-9_]*\}' "$tmp" >/dev/null; then
    rm -f "$tmp"
    die "Refusing to write ${target_file}; contains unresolved placeholders or blank values"
  fi

  mv "$tmp" "$target_file"
  chmod 600 "$target_file"
  log "Wrote ${target_file}"
}

write_reference_file() {
  local env_file
  env_file="${PROJECT_DIR}/.env.local"
  if [[ "$MODE" == "production" ]]; then
    env_file="${PROJECT_DIR}/.env.production"
  fi

  [[ -f "$SECRETS_FILE" ]] || die "Missing secrets file while generating reference"
  [[ -f "$env_file" ]] || die "Missing env file while generating reference"

  {
    echo "# Auto-generated setup reference"
    echo "# Contains generated defaults and secrets used by setup"
    echo "# Mode: ${MODE}"
    echo
    cat "$SECRETS_FILE"
    echo
    cat "$env_file"
  } > "$REFERENCE_FILE"
  chmod 600 "$REFERENCE_FILE"
  log "Wrote setup reference: ${REFERENCE_FILE}"
}

main() {
  log "Starting bootstrap in ${MODE^^} mode"
  install_dependencies
  generate_secrets_file
  render_env_file
  write_reference_file

  cat <<MSG
--------------------------------------------
Metabolic OS Setup Complete
--------------------------------------------
Mode: ${MODE^^}
URL: $([[ "$MODE" == "production" ]] && echo "https://yourdomain.com" || echo "http://localhost:3000")

Admin Login:
Email: admin@local
Password: ********

Secrets saved in:
${SECRETS_FILE}

Full setup reference saved in:
${REFERENCE_FILE}
--------------------------------------------
MSG
}

main "$@"
