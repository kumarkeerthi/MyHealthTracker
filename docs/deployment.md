# Deployment

## Components
- `docker-compose.prod.yml` orchestrates db, redis, backend, celery, frontend, nginx, watchdog.
- Backend exposes `/health` and `/metrics`.

## Security and reliability
- Restart policy: `unless-stopped`
- Health checks for DB, Redis, backend
- Log rotation via Docker logging options
- Optional webhook alerting using `deploy/container_alert.sh`

## Environment
Configure `.env` with:
- database + redis credentials
- OpenAI keys
- JWT settings
- CORS allowlist
- rate-limit and LLM quotas

## Rollout
1. `./deploy.sh`
2. Verify `docker compose -f docker-compose.prod.yml ps`
3. Probe endpoints: `/health`, `/metrics`
