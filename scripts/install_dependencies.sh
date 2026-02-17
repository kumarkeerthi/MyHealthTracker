#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="local"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prod) MODE="production" ;;
    -h|--help)
      cat <<USAGE
Usage: ./scripts/install_dependencies.sh [--prod]
  --prod   Install production dependencies (includes nginx, certbot, rsync)
USAGE
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
  shift
done

log() { printf '[deps] %s\n' "$*"; }
die() { printf '[deps][error] %s\n' "$*" >&2; exit 1; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

ensure_package() {
  local cmd="$1"
  local pkg="$2"
  if command_exists "$cmd"; then
    return 0
  fi

  if ! command_exists apt-get; then
    die "Cannot install ${pkg}: apt-get is unavailable"
  fi

  log "Installing ${pkg}"
  apt-get update -y >/dev/null
  DEBIAN_FRONTEND=noninteractive apt-get install -y "$pkg" >/dev/null
  command_exists "$cmd" || die "Failed to install ${pkg}"
}

main() {
  cd "$PROJECT_DIR"

  ensure_package curl curl
  ensure_package openssl openssl
  ensure_package docker docker.io
  ensure_package python3 python3

  if ! docker compose version >/dev/null 2>&1; then
    if command_exists apt-get; then
      log "Installing docker compose plugin"
      DEBIAN_FRONTEND=noninteractive apt-get install -y docker-compose-plugin >/dev/null
    fi
    docker compose version >/dev/null 2>&1 || die "Docker Compose plugin is required"
  fi

  if [[ "$MODE" == "production" ]]; then
    ensure_package nginx nginx
    ensure_package certbot certbot
    ensure_package rsync rsync
  fi

  log "Dependency installation complete (${MODE})."
}

main "$@"
