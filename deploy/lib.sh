#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_DIR}/.env"
LOG_DIR="/logs"
BOOTSTRAP_LOG="${LOG_DIR}/bootstrap.log"
DEPLOY_LOG="${LOG_DIR}/deploy.log"
DEPLOY_DIR="${PROJECT_DIR}/deploy"
NGINX_TEMPLATE="${DEPLOY_DIR}/nginx.template.conf"
NGINX_RENDERED_CONF="${DEPLOY_DIR}/nginx.conf"

log() { printf "[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
warn() { printf "[WARN] %s\n" "$*"; }
die() { printf "[ERROR] %s\n" "$*" >&2; exit 1; }

ensure_logs_dir() {
  mkdir -p "${LOG_DIR}"
  touch "${BOOTSTRAP_LOG}" "${DEPLOY_LOG}"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

os_is_ubuntu_compatible() {
  [[ -f /etc/os-release ]] || return 1
  # shellcheck disable=SC1091
  source /etc/os-release
  [[ "${ID:-}" == "ubuntu" || "${ID_LIKE:-}" == *"ubuntu"* || "${ID_LIKE:-}" == *"debian"* ]]
}

os_version_supported() {
  [[ -f /etc/os-release ]] || return 1
  # shellcheck disable=SC1091
  source /etc/os-release
  local version="${VERSION_ID:-0}"
  awk -v v="$version" 'BEGIN {exit !(v+0 >= 20.04)}'
}

ensure_root_or_sudo() {
  if [[ "${EUID}" -eq 0 ]]; then
    return 0
  fi
  require_cmd sudo
  exec sudo -E bash "$0" "$@"
}

apt_install_missing() {
  local packages=()
  for pkg in "$@"; do
    dpkg -s "$pkg" >/dev/null 2>&1 || packages+=("$pkg")
  done

  if (( ${#packages[@]} > 0 )); then
    log "Installing missing packages: ${packages[*]}"
    apt-get install -y "${packages[@]}"
  fi
}

random_hex() {
  local length="$1"
  openssl rand -hex $(( length / 2 ))
}

random_base64() {
  local bytes="$1"
  openssl rand -base64 "$bytes" | tr -d '\n'
}

validate_required_env() {
  local missing=()
  for key in "$@"; do
    if [[ -z "${!key:-}" ]]; then
      missing+=("$key")
    fi
  done

  if (( ${#missing[@]} > 0 )); then
    die "Missing required .env values: ${missing[*]}"
  fi
}

validate_openai_key() {
  [[ "${OPENAI_API_KEY:-}" == sk-* ]] || die "OPENAI_API_KEY must start with sk-."
}

get_primary_public_ip() {
  local ip
  ip="$(curl -fsS --max-time 8 https://api.ipify.org || true)"
  if [[ -z "$ip" ]]; then
    ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  fi
  printf "%s" "$ip"
}

resolve_domain_ip() {
  local domain="$1"
  getent ahosts "$domain" | awk '/STREAM/ {print $1; exit}'
}

validate_domain_points_here() {
  local domain="$1"
  local resolved_ip server_ip
  resolved_ip="$(resolve_domain_ip "$domain")"
  [[ -n "$resolved_ip" ]] || die "Domain ${domain} does not resolve."
  server_ip="$(get_primary_public_ip)"
  [[ -n "$server_ip" ]] || die "Could not determine this server IP to validate ${domain}."
  if [[ "$resolved_ip" != "$server_ip" ]]; then
    die "Domain ${domain} resolves to ${resolved_ip}, but server IP is ${server_ip}. Update DNS before deployment."
  fi
}

validate_ports_available() {
  for port in 80 443; do
    if ss -ltnH "( sport = :${port} )" 2>/dev/null | grep -q .; then
      die "Port ${port} is already in use."
    fi
  done
}

validate_docker_running() {
  require_cmd docker
  if ! docker info >/dev/null 2>&1; then
    die "Docker daemon is not running. Start docker and retry."
  fi
}

render_nginx_config() {
  local domain="$1"
  [[ -f "$NGINX_TEMPLATE" ]] || die "Missing nginx template at ${NGINX_TEMPLATE}."
  sed "s/__APP_DOMAIN__/${domain}/g" "$NGINX_TEMPLATE" > "$NGINX_RENDERED_CONF"
}
