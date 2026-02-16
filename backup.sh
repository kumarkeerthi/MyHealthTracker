#!/usr/bin/env bash
set -euo pipefail

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
UPLOADS_DIR="${UPLOADS_DIR:-./app/data/uploads}"
DB_CONTAINER="${DB_CONTAINER:-$(docker compose ps -q db)}"
POSTGRES_DB="${POSTGRES_DB:-metabolic}"
POSTGRES_USER="${POSTGRES_USER:-metabolic}"
S3_URI="${S3_URI:-}"

mkdir -p "$BACKUP_DIR"
WORK_DIR="$(mktemp -d)"

DB_DUMP="$WORK_DIR/postgres_${TIMESTAMP}.sql"
ARCHIVE_FILE="$BACKUP_DIR/myhealthtracker_backup_${TIMESTAMP}.tar.gz"

echo "[backup] dumping PostgreSQL..."
if [[ -n "$DB_CONTAINER" ]]; then
  docker exec "$DB_CONTAINER" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$DB_DUMP"
else
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$DB_DUMP"
fi

echo "[backup] archiving uploads + dump..."
tar -czf "$ARCHIVE_FILE" -C "$WORK_DIR" "$(basename "$DB_DUMP")" -C "$(dirname "$UPLOADS_DIR")" "$(basename "$UPLOADS_DIR")"

echo "[backup] created $ARCHIVE_FILE"

if [[ -n "$S3_URI" ]]; then
  echo "[backup] uploading to S3: $S3_URI"
  aws s3 cp "$ARCHIVE_FILE" "$S3_URI/"
fi

rm -rf "$WORK_DIR"
