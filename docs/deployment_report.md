# Deployment Report

## Scope reviewed

- `setup.sh`
- `update.sh`
- `docker-compose.prod.yml`
- Nginx templates/configs
- Certbot hooks and renewal automation
- Rollback and dry-run test scripts

## Key corrections delivered

1. Replaced deployment setup with a strict-mode, production-safe bootstrap flow.
2. Added Certbot hooks and a systemd timer for unattended renewals.
3. Converted compose production spec to Compose v2 conventions and improved service health checks.
4. Added temporary HTTP-only Nginx bootstrap config to prevent first-cert deadlock.
5. Added rollback and dry-run validation scripts for safer operations.

## Validation performed

- Compose syntax validation.
- Shell syntax checks for updated scripts.
- Verified executable bits on operational scripts/hooks.

## Operational commands (health checks)

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production ps
docker compose -f docker-compose.prod.yml --env-file .env.production logs --tail=200 nginx backend
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T nginx nginx -t
curl -I https://YOUR_DOMAIN
curl -kfsS https://YOUR_DOMAIN/health
sudo certbot renew --dry-run
systemctl list-timers | grep myhealthtracker-cert-renew
```
