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

### `.env` values you should override

`./setup.sh` creates `.env` only if it does not already exist. Before sharing your environment or deploying, review and override these values:

- `POSTGRES_PASSWORD` and `DATABASE_URL`
  - Keep the same password in both fields.
  - Example:
    - `POSTGRES_PASSWORD=my_local_db_password_123`
    - `DATABASE_URL=postgresql+psycopg2://metabolic:my_local_db_password_123@db:5432/metabolic`
- `JWT_SECRET` and `HEALTH_SYNC_SIGNING_SECRET`
  - Replace dev secrets with long random strings.
  - Example:
    - `JWT_SECRET=7f4f4f8f3e0b4cf997f62f4d6bd0e36ca8f64c4a2e73d8d4f9b9ddf5e8d54111`
    - `HEALTH_SYNC_SIGNING_SECRET=b7aa2e4fcb0f4f2ea0b90a8f111fa4b7dcb15dbf265f4637ab534077388cc4e9`
- `OPENAI_API_KEY`
  - Set if you want AI-powered features.
  - Example: `OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx`
- `CORS_ALLOWED_ORIGINS` and `NEXT_PUBLIC_API_BASE_URL`
  - Match the frontend URL(s) and API URL for your environment.
  - Example (local):
    - `CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`
    - `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

For production, start from `.env.example` and override **all** placeholder values such as:

- `APP_DOMAIN` / `DOMAIN` (example: `health.example.com`)
- `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, and all corresponding URLs
- `JWT_SECRET` (64+ random characters)
- `OPENAI_API_KEY`
- `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`
- `ADMIN_EMAIL`, `ADMIN_PASSWORD_HASH`
- `FOOD_IMAGE_PUBLIC_BASE_URL` (example: `https://health.example.com/uploads`)

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
