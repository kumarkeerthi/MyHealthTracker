#!/usr/bin/env sh
set -eu

WATCHED_CONTAINERS="${WATCHED_CONTAINERS:-backend,celery,db,redis,frontend,nginx}"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"

for name in $(echo "$WATCHED_CONTAINERS" | tr ',' ' '); do
  if ! docker ps --format '{{.Names}}' | grep -Eq "(^|_)${name}($|_)"; then
    message="[ALERT] Container appears down: ${name}"
    echo "$message"
    if [ -n "$ALERT_WEBHOOK_URL" ]; then
      curl -fsS -X POST -H 'Content-Type: application/json' \
        -d "{\"text\":\"${message}\"}" "$ALERT_WEBHOOK_URL" >/dev/null || true
    fi
  fi
done
