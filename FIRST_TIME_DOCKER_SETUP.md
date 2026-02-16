# First-Time Setup (Super Easy Docker Guide)

This guide gets the full app running in Docker for the first time: **API + PostgreSQL + Frontend**.

## 1) Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose v2)
- At least 4 GB free RAM for containers

Quick checks:

```bash
docker --version
docker compose version
```

---

## 2) Create your `.env` file (required)

From the project root, create `.env`:

```bash
cp .env.example .env
```

Then edit `.env` and set values for your environment.

### Minimum values you should set now

```dotenv
# --- Database ---
POSTGRES_DB=metabolic
POSTGRES_USER=metabolic
POSTGRES_PASSWORD=metabolic

# SQLAlchemy URL used by API container
DATABASE_URL=postgresql+psycopg2://metabolic:metabolic@db:5432/metabolic

# --- API security (CHANGE in real environments) ---
JWT_SECRET=CHANGE_ME_TO_A_LONG_RANDOM_SECRET
HEALTH_SYNC_SIGNING_SECRET=CHANGE_ME_TO_A_DIFFERENT_LONG_RANDOM_SECRET

# --- App behavior ---
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
LLM_CACHE_TTL_SECONDS=900
REQUIRE_HTTPS=false
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# --- Frontend ---
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

> Notes:
> - Keep `OPENAI_API_KEY` empty if you don't need LLM endpoints right away.
> - For production, use strong secrets and set `REQUIRE_HTTPS=true`.

---

## 3) Start everything

```bash
docker compose up --build -d
```

This starts:
- `db` (PostgreSQL)
- `api` (FastAPI backend on port `8000`)
- `frontend` (Next.js app on port `3000`)

---

## 4) Verify it works

API health:

```bash
curl http://localhost:8000/health
```

Open frontend:

- http://localhost:3000

Follow logs (optional):

```bash
docker compose logs -f api frontend db
```

---

## 5) Common first-time commands

Stop:

```bash
docker compose down
```

Stop + remove DB data (full reset):

```bash
docker compose down -v
```

Rebuild after code/dependency changes:

```bash
docker compose up --build -d
```

---

## 6) Troubleshooting

### Port already in use
- If `3000`, `5432`, or `8000` is occupied, stop the conflicting process/container.
- Or change port mappings in `docker-compose.yml`.

### Frontend cannot reach API
- Ensure in `.env`:
  - `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
- Rebuild frontend:

```bash
docker compose up --build -d frontend
```

### Database connection errors
- Ensure `DATABASE_URL` host is `db` (the Docker service name), not `localhost`.

---

## 7) Recommended production hardening (before real deployment)

- Change all default secrets/passwords.
- Use managed secrets (not plain `.env` committed to git).
- Set `REQUIRE_HTTPS=true`.
- Restrict `CORS_ALLOWED_ORIGINS` to your real domain(s).
- Use `docker-compose.prod.yml` + reverse proxy/TLS setup from `deploy/`.
