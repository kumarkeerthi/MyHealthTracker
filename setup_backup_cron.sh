#!/usr/bin/env bash
set -euo pipefail

CRON_SCHEDULE="${CRON_SCHEDULE:-0 2 * * *}"
PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
BACKUP_CMD="cd $PROJECT_DIR && ./backup.sh >> $PROJECT_DIR/logs/backup.log 2>&1"

mkdir -p "$PROJECT_DIR/logs"
( crontab -l 2>/dev/null | grep -v "backup.sh"; echo "$CRON_SCHEDULE $BACKUP_CMD" ) | crontab -
echo "Backup cron installed: $CRON_SCHEDULE"
