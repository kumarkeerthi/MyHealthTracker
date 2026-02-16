#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup_archive.tar.gz>"
  exit 1
fi

ARCHIVE_FILE="$1"
RESTORE_DIR="$(mktemp -d)"
UPLOADS_DIR="${UPLOADS_DIR:-./app/data/uploads}"
DB_CONTAINER="${DB_CONTAINER:-$(docker compose ps -q db)}"
POSTGRES_DB="${POSTGRES_DB:-metabolic}"
POSTGRES_USER="${POSTGRES_USER:-metabolic}"

tar -xzf "$ARCHIVE_FILE" -C "$RESTORE_DIR"
SQL_DUMP="$(find "$RESTORE_DIR" -name 'postgres_*.sql' | head -n 1)"
UPLOADS_SNAPSHOT="$(find "$RESTORE_DIR" -maxdepth 1 -type d -name 'uploads' | head -n 1)"

if [[ -z "$SQL_DUMP" ]]; then
  echo "SQL dump not found in archive"
  exit 1
fi

echo "[restore] restoring PostgreSQL from $SQL_DUMP"
if [[ -n "$DB_CONTAINER" ]]; then
  cat "$SQL_DUMP" | docker exec -i "$DB_CONTAINER" psql -U "$POSTGRES_USER" "$POSTGRES_DB"
else
  psql -U "$POSTGRES_USER" "$POSTGRES_DB" < "$SQL_DUMP"
fi

if [[ -n "$UPLOADS_SNAPSHOT" ]]; then
  echo "[restore] restoring uploads"
  rm -rf "$UPLOADS_DIR"
  mkdir -p "$(dirname "$UPLOADS_DIR")"
  cp -R "$UPLOADS_SNAPSHOT" "$UPLOADS_DIR"
fi

rm -rf "$RESTORE_DIR"
echo "[restore] completed"
