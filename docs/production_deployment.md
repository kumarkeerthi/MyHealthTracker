# Production Deployment Guide (Ubuntu 22.04+)

## What was wrong in the original setup

- `docker-compose.prod.yml` used mixed env-file patterns (`generated_secrets.env` + `.env.production`) that made production drift-prone.
- Nginx TLS config depended on existing cert files at first boot; this can crash Nginx before cert issuance.
- Certbot lifecycle was incomplete (no robust pre/post/deploy hooks and no guaranteed scheduler).
- Update workflow had limited rollback context and weak health validation.
- DNS validation and deployment preflight checks were not centralized for a reliable production bootstrap.

## What was fixed

- Added strict, step-logged production installer in `setup.sh` with:
  - Docker daemon startup checks.
  - Compose v2 validation.
  - DNS resolution check against server public IP.
  - Two-phase Nginx bootstrap (HTTP-only -> TLS config).
  - Automated cert issuance with Certbot hooks.
  - systemd timer installation for renewal.
- Reworked `docker-compose.prod.yml` to current Compose v2 style (no `version:`), clearer health checks, and corrected certificate volume mounts.
- Added certbot hooks:
  - `deploy/certbot-hooks/pre-hook.sh` (stop nginx)
  - `deploy/certbot-hooks/post-hook.sh` (restart nginx)
  - `deploy/certbot-hooks/deploy-hook.sh` (sync certs + reload nginx)
- Added `rollback.sh` for commit-based rollback.
- Added `scripts/deployment_dry_run.sh` for non-destructive validation.
- Added `.env.production.example` with required production keys.

## Why these fixes were required (technical rationale)

- Nginx cannot load TLS blocks without certificate files; using a temporary HTTP config prevents first-run deadlock.
- Certbot standalone needs exclusive access to port 80; stopping Nginx in hooks avoids intermittent challenge failures.
- systemd timer provides deterministic, host-level renewal independent of container uptime.
- Explicit health checks and update snapshots reduce MTTR during regressions.

## First install and deployment

```bash
cp .env.production.example .env.production
# edit .env.production with real values

chmod +x setup.sh update.sh rollback.sh scripts/deployment_dry_run.sh
./setup.sh --production
```

## Update deployment

```bash
./update.sh
```

## Add a new domain

1. Update DNS A/AAAA to this server.
2. Set `DOMAIN` and `APP_DOMAIN` in `.env.production`.
3. Re-run setup:

```bash
./setup.sh --production
```

## Rollback

```bash
./rollback.sh <git-tag-or-commit>
```

## Monitor SSL renewal

```bash
systemctl status myhealthtracker-cert-renew.timer
journalctl -u myhealthtracker-cert-renew.service -n 100 --no-pager
sudo certbot renew --dry-run
```

## DNS verification commands

```bash
nslookup YOUR_DOMAIN
getent ahosts YOUR_DOMAIN
curl -4 ifconfig.me
```

## Validation checklist

```bash
./scripts/deployment_dry_run.sh
curl -I http://YOUR_DOMAIN
curl -I https://YOUR_DOMAIN
curl -kfsS https://YOUR_DOMAIN/health
docker compose -f docker-compose.prod.yml --env-file .env.production ps
```
