# Unified Setup Guide

Use **one command** for setup: `./setup.sh`.

This project supports two environments, both handled by the same script:

- **Local development (default):** starts backend + frontend + database with Docker Compose.
- **Production:** runs bootstrap + deployment flow.

---

## Quick start (local, recommended)

From repository root:

```bash
chmod +x setup.sh
./setup.sh
```

What this does automatically:

1. Verifies Docker + Docker Compose are available.
2. Creates `.env` with local defaults if missing.
3. Starts the full stack: `db`, `api`, `frontend`.
4. Waits for API health check (`/health`).

After it finishes:

- Frontend: http://localhost:3000
- API: http://localhost:8000
- Health: http://localhost:8000/health

---

## Production setup

Run:

```bash
./setup.sh --production
```

This executes:

1. `./bootstrap.sh` (interactive provisioning + env generation)
2. `./deploy.sh` (production deploy)

Use this only for real server deployment.

---

## Command reference

- Start everything locally:

```bash
./setup.sh
```

- Explicit local mode:

```bash
./setup.sh --local
```

- Production mode:

```bash
./setup.sh --production
```

- Tail logs:

```bash
docker compose logs -f api frontend db
```

- Stop containers:

```bash
docker compose down
```

- Full reset (including database volume):

```bash
docker compose down -v
```

---

## Which command should I run?

- If you are developing locally: **`./setup.sh`**
- If you are deploying to production server: **`./setup.sh --production`**

Do **not** run `deploy.sh` directly unless you intentionally want the advanced production workflow.
