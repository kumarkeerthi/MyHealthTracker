# Upgrade Guide

## Pre-upgrade checklist
- Run `./backup.sh`
- Validate artifact presence in local/S3 storage
- Capture current container state (`docker compose ps`)

## Upgrade steps
1. Pull latest code.
2. Update `.env` with new variables if introduced.
3. Rebuild services:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```
4. Validate health and metrics endpoints.
5. Inspect logs for migration/runtime errors.

## Rollback
- Restore previous image tags or git revision.
- Run `./restore.sh <backup>` if data rollback is required.
- Re-validate `/health` and critical API paths.
