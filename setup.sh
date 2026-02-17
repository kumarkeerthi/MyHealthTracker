#!/usr/bin/env bash
# One-click setup entrypoint for MyHealthTracker.
# Orchestrates dependency installation, configuration generation, and deployment.

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/setup.log"
MODE="local"
FORCE="false"
REGEN_SECRETS="false"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

log() { printf '[setup] %s\n' "$*"; }
die() { printf '[setup][error] %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'USAGE'
Usage:
  ./setup.sh [--prod] [--force] [--regen-secrets]

Flow:
  1) Install dependencies
  2) Configure environment/secrets
  3) Deploy and initialize services

Notes:
- The only interactive prompt is OPENAI_API_KEY (unless already exported).
- Production APP_DOMAIN defaults to localhost unless APP_DOMAIN is exported.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prod|--production) MODE="production" ;;
    --force) FORCE="true" ;;
    --regen-secrets) REGEN_SECRETS="true" ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
  shift
done

run_install_dependencies() {
  log "Step 1/3: Installing dependencies"
  if [[ "$MODE" == "production" ]]; then
    "$PROJECT_DIR/scripts/install_dependencies.sh" --prod
  else
    "$PROJECT_DIR/scripts/install_dependencies.sh"
  fi
}

run_configuration() {
  log "Step 2/3: Generating configuration and defaults"
  local args=()
  if [[ "$MODE" == "production" ]]; then
    args+=(--prod)
  fi
  if [[ "$FORCE" == "true" ]]; then
    args+=(--force)
  fi
  if [[ "$REGEN_SECRETS" == "true" ]]; then
    args+=(--regen-secrets)
  fi
  "$PROJECT_DIR/bootstrap.sh" "${args[@]}"
}

run_deployment() {
  log "Step 3/3: Deploying containers and bootstrapping database"
  if [[ "$MODE" == "production" ]]; then
    "$PROJECT_DIR/deploy.sh" --prod
  else
    "$PROJECT_DIR/deploy.sh"
  fi
}

main() {
  cd "$PROJECT_DIR"
  run_install_dependencies
  run_configuration
  run_deployment
  log "One-click setup completed successfully (${MODE})."
}

main "$@"
