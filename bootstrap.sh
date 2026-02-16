#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${PROJECT_DIR}/deploy/lib.sh"

exec > >(tee -a "$BOOTSTRAP_LOG") 2>&1

install_dependencies() {
  require_cmd apt-get
  apt-get update
  apt_install_missing curl git openssl nginx ufw ca-certificates gnupg lsb-release python3 python3-bcrypt

  if ! command -v docker >/dev/null 2>&1; then
    log "Installing Docker Engine + Compose plugin"
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    # shellcheck disable=SC1091
    source /etc/os-release
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
      | tee /etc/apt/sources.list.d/docker.list >/dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  else
    apt_install_missing docker-compose-plugin
  fi

  systemctl enable --now docker
}

create_required_directories() {
  mkdir -p /data/postgres /data/uploads /backups /logs
  chmod 755 /data /data/postgres /data/uploads /backups /logs
}

prompt_default() {
  local prompt="$1"
  local default_value="$2"
  local out
  read -rp "$prompt" out
  printf "%s" "${out:-$default_value}"
}

prompt_non_empty() {
  local prompt="$1"
  local out
  while true; do
    read -rp "$prompt" out
    if [[ -n "$out" ]]; then
      printf "%s" "$out"
      return
    fi
    warn "This value is required."
  done
}

prompt_openai_key() {
  local key
  while true; do
    cat <<'MSG'
Enter your OpenAI API key.
To retrieve:
1. Go to https://platform.openai.com
2. Click API Keys
3. Create new secret key
4. Paste here
MSG
    read -rsp "OPENAI_API_KEY: " key
    echo
    if [[ "$key" == sk-* ]]; then
      printf "%s" "$key"
      return
    fi
    warn "Invalid key format. OPENAI_API_KEY must start with sk-."
  done
}

prompt_admin_password_hash() {
  local password confirm hash
  while true; do
    read -rsp "Create admin password: " password
    echo
    read -rsp "Confirm admin password: " confirm
    echo
    [[ -n "$password" ]] || { warn "Admin password cannot be empty."; continue; }
    [[ "$password" == "$confirm" ]] || { warn "Passwords do not match."; continue; }
    hash="$(python3 - <<'PY' "$password"
import bcrypt, sys
pwd = sys.argv[1].encode("utf-8")
print(bcrypt.hashpw(pwd, bcrypt.gensalt(rounds=12)).decode("utf-8"))
PY
)"
    printf "%s" "$hash"
    return
  done
}

generate_vapid_keys() {
  local private_key public_key
  private_key="$(random_base64 32)"
  public_key="$(random_base64 32)"
  printf "%s;%s" "$public_key" "$private_key"
}

write_env_file() {
  local postgres_db postgres_user postgres_password openai_api_key app_domain
  local cors_allowed_origins api_base_url jwt_secret redis_password admin_email admin_password_hash
  local vapid_public_key vapid_private_key vapid_subject

  postgres_db="$(prompt_default 'Enter database name (default: metabolic_db): ' 'metabolic_db')"
  postgres_user="$(prompt_default 'Enter database username (default: metabolic_user): ' 'metabolic_user')"
  postgres_password="$(random_hex 32)"
  openai_api_key="$(prompt_openai_key)"
  app_domain="$(prompt_non_empty 'Enter your domain (example: app.yourdomain.com): ')"
  admin_email="$(prompt_non_empty 'Create admin email: ')"
  admin_password_hash="$(prompt_admin_password_hash)"

  cors_allowed_origins="https://${app_domain}"
  api_base_url="https://${app_domain}/api"
  jwt_secret="$(random_hex 64)"
  redis_password="$(random_hex 32)"
  vapid_subject="mailto:${admin_email}"

  IFS=';' read -r vapid_public_key vapid_private_key <<<"$(generate_vapid_keys)"

  cat > "$ENV_FILE" <<EOF_ENV
ENVIRONMENT=production
APP_DOMAIN=${app_domain}
DOMAIN=${app_domain}
POSTGRES_DB=${postgres_db:-metabolic_db}
POSTGRES_USER=${postgres_user:-metabolic_user}
POSTGRES_PASSWORD=${postgres_password}
DATABASE_URL=postgresql+psycopg2://${postgres_user:-metabolic_user}:${postgres_password}@db:5432/${postgres_db:-metabolic_db}
REDIS_PASSWORD=${redis_password}
REDIS_URL=redis://:${redis_password}@redis:6379/0
CELERY_BROKER_URL=redis://:${redis_password}@redis:6379/0
CELERY_RESULT_BACKEND=redis://:${redis_password}@redis:6379/0
OPENAI_API_KEY=${openai_api_key}
OPENAI_MODEL=gpt-4o-mini
CORS_ALLOWED_ORIGINS=${cors_allowed_origins:-https://${app_domain}}
NEXT_PUBLIC_API_BASE_URL=${api_base_url}
JWT_SECRET=${jwt_secret}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60
REQUIRE_HTTPS=true
VAPID_PUBLIC_KEY=${vapid_public_key}
VAPID_PRIVATE_KEY=${vapid_private_key}
VAPID_SUBJECT=${vapid_subject}
ADMIN_EMAIL=${admin_email}
ADMIN_PASSWORD_HASH=${admin_password_hash}
LOG_LEVEL=INFO
LOG_DIR=/logs
MAX_FOOD_IMAGE_BYTES=5000000
FOOD_IMAGE_UPLOAD_DIR=/data/uploads
FOOD_IMAGE_PUBLIC_BASE_URL=https://${app_domain}/uploads
EOF_ENV

  chmod 600 "$ENV_FILE"
  log "Wrote ${ENV_FILE}"
}

validate_bootstrap_output() {
  # shellcheck disable=SC1090
  source "$ENV_FILE"

  validate_required_env POSTGRES_DB POSTGRES_USER CORS_ALLOWED_ORIGINS NEXT_PUBLIC_API_BASE_URL OPENAI_API_KEY APP_DOMAIN JWT_SECRET REDIS_PASSWORD ADMIN_EMAIL ADMIN_PASSWORD_HASH
  validate_openai_key
  validate_domain_points_here "$APP_DOMAIN"
  validate_ports_available
  validate_docker_running
}

main() {
  ensure_logs_dir
  ensure_root_or_sudo "$@"

  if ! os_is_ubuntu_compatible; then
    warn "Non-Ubuntu OS detected. Continuing, but this bootstrap is tuned for Ubuntu 20.04+."
  elif ! os_version_supported; then
    warn "Ubuntu version appears below 20.04. Continuing, but compatibility is not guaranteed."
  fi

  log "Starting bootstrap. Logs: ${BOOTSTRAP_LOG}"
  install_dependencies
  create_required_directories
  write_env_file
  validate_bootstrap_output

  log "Bootstrap complete. Next step: ./deploy.sh"
}

main "$@"
