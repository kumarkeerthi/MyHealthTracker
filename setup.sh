#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${PROJECT_DIR}/.env"

usage() {
  cat <<'USAGE'
Usage: ./setup.sh [--local|--production]

Modes:
  --local       Start complete local stack (backend + frontend + database) using Docker Compose.
                This is the default mode.
  --production  Run production bootstrap + deploy flow (interactive).

Examples:
  ./setup.sh
  ./setup.sh --local
  ./setup.sh --production
USAGE
}

log() {
  printf '[setup] %s\n' "$1"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command '$1' is not installed or not in PATH." >&2
    exit 1
  fi
}

create_local_env_if_missing() {
  if [[ -f "$ENV_FILE" ]]; then
    log ".env already exists. Keeping existing configuration."
    return
  fi

  log "No .env found. Creating a local-development .env with safe defaults."
  cat > "$ENV_FILE" <<'EOF_ENV'
POSTGRES_DB=metabolic
POSTGRES_USER=metabolic
POSTGRES_PASSWORD=metabolic
DATABASE_URL=postgresql+psycopg2://metabolic:metabolic@db:5432/metabolic

JWT_SECRET=dev_only_change_me
HEALTH_SYNC_SIGNING_SECRET=dev_only_change_me_too

OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
LLM_CACHE_TTL_SECONDS=900

REQUIRE_HTTPS=false
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
EOF_ENV

  log "Created .env for local use. Edit it if you need custom settings."
}

wait_for_api_health() {
  local max_attempts=40
  local attempt=1

  log "Waiting for API health endpoint at http://localhost:8000/health ..."
  while (( attempt <= max_attempts )); do
    if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
      log "API is healthy."
      return 0
    fi

    sleep 2
    ((attempt++))
  done

  echo "Warning: API health check did not pass in time. Check logs: docker compose logs -f api" >&2
  return 1
}

run_local_setup() {
  require_cmd docker
  require_cmd curl

  if ! docker compose version >/dev/null 2>&1; then
    echo "Error: Docker Compose v2 is required (docker compose)." >&2
    exit 1
  fi

  create_local_env_if_missing

  log "Starting full local stack (db + api + frontend) with Docker Compose..."
  (
    cd "$PROJECT_DIR"
    docker compose up --build -d
  )

  wait_for_api_health || true

  cat <<'EOF_DONE'

Setup complete.

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API health: http://localhost:8000/health

Useful commands:
  docker compose logs -f api frontend db
  docker compose down
  docker compose down -v   # full reset (includes database volume)
EOF_DONE
}

run_production_setup() {
  require_cmd bash
  log "Starting production setup (interactive)."
  log "This runs bootstrap.sh --prod first, then deploy.sh --prod."

  (
    cd "$PROJECT_DIR"
    ./bootstrap.sh --prod
    ./deploy.sh --prod
  )
}

main() {
  local mode="local"

  if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then
    usage
    exit 0
  fi

  case "${1:-}" in
    ""|--local)
      mode="local"
      ;;
    --production)
      mode="production"
      ;;
    *)
      echo "Unknown option: ${1}" >&2
      usage
      exit 1
      ;;
  esac

  if [[ "$mode" == "local" ]]; then
    run_local_setup
  else
    run_production_setup
  fi
}

main "$@"
