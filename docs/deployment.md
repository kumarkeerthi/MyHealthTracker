# Deployment Guide

This document outlines production deployment structure, required configuration, rollout flow, and basic verification.

## Production stack components

`docker-compose.prod.yml` orchestrates:

- `db` (PostgreSQL)
- `redis`
- `backend` (FastAPI)
- `celery` worker
- `frontend` (Next.js)
- `nginx` reverse proxy
- `watchdog`/alert helper

## Prerequisites

- Docker + Docker Compose available on host.
- `.env` prepared with secure production values.
- DNS/TLS plan ready for public endpoint exposure.
- Backup procedure validated before first production rollout.

## Required environment configuration

At minimum configure:

- Database and Redis connection settings
- OpenAI model/key settings (if LLM endpoints enabled)
- JWT and auth values
- CORS allowlist
- Rate limiting and quota settings
- Push/VAPID keys if push is enabled

## Security and reliability controls in deployment

- Container restart policy: `unless-stopped`
- Health checks for key services
- Log rotation through container logging options
- Optional container alert webhook (`deploy/container_alert.sh`)
- Nginx reverse proxy for edge routing and TLS termination patterns

## Standard rollout

1. Run guided deploy tool:

   ```bash
   ./deploy.sh
   ```

2. Confirm service status:

   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```

3. Probe health + metrics:
   - `GET /health`
   - `GET /metrics`

4. Run critical smoke tests (auth, log-food, daily summary, notification path).

## Update flow

For normal updates:

```bash
./update.sh
```

This should rebuild/restart as configured and re-check service health.

## Rollback notes

- Keep prior image tags / known-good git revision accessible.
- Restore data from backup only when rollback requires data reversal.
- After rollback, validate health, metrics, and key user flows.

## Post-deployment monitoring

- Watch logs for error spikes in first 30 minutes.
- Validate scheduler-triggered tasks execute.
- Confirm queue depth and worker health (Redis/Celery paths).
- Track p95 latency and non-2xx rate where metrics are available.
