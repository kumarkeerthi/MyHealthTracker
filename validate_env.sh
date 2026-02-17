#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="local"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prod) MODE="production" ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
  shift
done

SECRETS_FILE="${PROJECT_DIR}/generated_secrets.env"
ENV_FILE="${PROJECT_DIR}/.env.local"
if [[ "$MODE" == "production" ]]; then
  ENV_FILE="${PROJECT_DIR}/.env.production"
fi

fail() { echo "[ERROR] $*" >&2; exit 1; }

[[ -f "$SECRETS_FILE" ]] || fail "Missing generated_secrets.env; run ./bootstrap.sh"
[[ -f "$ENV_FILE" ]] || fail "Missing $(basename "$ENV_FILE"); run ./bootstrap.sh"

set -a
# shellcheck disable=SC1090
source "$SECRETS_FILE"
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

required=(POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB REDIS_PASSWORD JWT_SECRET INTERNAL_API_KEY SESSION_SECRET VAPID_PUBLIC_KEY VAPID_PRIVATE_KEY OPENAI_API_KEY)
for key in "${required[@]}"; do
  [[ -n "${!key:-}" ]] || fail "Required variable is empty: ${key}"
done

for key in "${required[@]}"; do
  [[ "${!key}" != "CHANGEME" ]] || fail "Placeholder value found for ${key}"
done

[[ "$OPENAI_API_KEY" == sk-* && ${#OPENAI_API_KEY} -ge 40 ]] || fail "OPENAI_API_KEY is invalid"

if ! docker info >/dev/null 2>&1; then
  fail "Docker daemon is not running"
fi

check_ports=(5432 6379)
if [[ "$MODE" == "local" ]]; then
  check_ports+=(3000 8000)
else
  check_ports+=(80 443)
fi

for port in "${check_ports[@]}"; do
  if ss -ltnH "( sport = :${port} )" 2>/dev/null | grep -q .; then
    echo "[WARN] Port ${port} already in use. Ensure this is expected (existing stack)."
  fi
done

echo "Environment validation passed (${MODE})."
