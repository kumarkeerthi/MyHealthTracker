# Upgrade Guide

Use this runbook for safe application upgrades with rollback readiness.

## 1) Pre-upgrade checklist

- Run and verify backup:
  - `./backup.sh`
- Confirm backup exists in expected local/offsite target.
- Capture current runtime state:
  - `docker compose -f docker-compose.prod.yml ps`
- Review `.env` changes introduced by the new release.
- Announce maintenance window for production upgrades.

## 2) Upgrade execution steps

1. Pull latest code revision.
2. Review release notes and migration scripts in `migrations/`.
3. Update `.env` values for any new feature/security variables.
4. Rebuild and restart services:

   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

5. Confirm containers are healthy:

   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```

6. Validate core endpoints:
   - `GET /health`
   - `GET /metrics`
7. Smoke-test critical workflows (auth, food logging, summaries, notifications).
8. Review backend logs for startup or migration errors.

## 3) Post-upgrade validation

- Ensure scheduler services are running as expected.
- Verify frontend can read API responses without CORS/auth regressions.
- Confirm background jobs (Celery/Redis paths) process tasks.
- Watch error rates for at least 15–30 minutes.

## 4) Rollback procedure

If severe regression occurs:

1. Roll back to previous image tags or prior git revision.
2. Restart stack with known-good artifact set.
3. If data rollback is required:

   ```bash
   ./restore.sh <backup-archive>
   ```

4. Re-run health checks and smoke tests.
5. Document root cause and corrective action before retrying upgrade.

## 5) Change management tips

- Upgrade in staging first with production-like data volume.
- Keep migration scripts idempotent where possible.
- Avoid combining infrastructure and feature migrations in one window.
- Maintain a release checklist in source control for repeatability.
