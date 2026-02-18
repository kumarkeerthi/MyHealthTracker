# Metabolic Intelligence Engine (Phase 1+ Extensions)

Clinical-grade metabolic intelligence backend built with FastAPI, SQLAlchemy, and PostgreSQL.

## Features
- Deterministic rule engine for insulin load scoring and nutrition validations.
- Configurable `metabolic_profiles` per user (seeded with defaults).
- Expanded exercise model (`exercise_category`, movement metadata, intensity, steps/calories).
- Expanded vitals model (`resting_hr`, `sleep_hours`, `waist_cm`, `hrv`, `steps_total`, `body_fat_percentage`).
- Apple Health automated sync endpoint (`POST /apple-sync`) with iOS Shortcut relay support and token auth.
- New profile, exercise summary, vitals summary, and external-event endpoints.
- WhatsApp webhook, notification event webhook, notification settings API, and automated coaching scheduler.

## Stack
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Docker / Docker Compose

## Run the full stack (recommended)
Use the unified one-click setup script:
```bash
./setup.sh
```

This executes dependency install, configuration generation, and deployment automatically.
Only `OPENAI_API_KEY` is prompted (unless already exported). Generated defaults are saved to `setup_reference.env`.

API available at: `http://localhost:8000`  
Frontend available at: `http://localhost:3000`

See `SETUP.md` for local and production setup flows.

## Endpoints
Existing:
- `POST /log-food`
- `GET /daily-summary`
- `POST /log-vitals`
- `POST /log-exercise`
- `GET /weekly-summary`
- `GET /health`

Added:
- `GET /profile`
- `PUT /profile`
- `GET /exercise-summary`
- `GET /vitals-summary`
- `POST /apple-sync`
- `POST /import-apple-health` (backward-compatible alias)
- `POST /external-event`
- `POST /llm/analyze`
- `GET /recipes`
- `GET /recipes/suggestions`
- `POST /whatsapp-message`
- `POST /notification-event`
- `GET /notification-settings`
- `PUT /notification-settings`



## LLM integration (Phase 3)
Set OpenAI credentials before starting API:
```bash
export OPENAI_API_KEY=<your_key>
export OPENAI_MODEL=gpt-4o-mini
export LLM_CACHE_TTL_SECONDS=900
```

`POST /llm/analyze` extracts food items, portion and estimated macros via strict JSON schema, then enforces deterministic fasting/carb/oil rules. If LLM fails, the service falls back to local food-catalog matching.

## Messaging + Notification layer (Phase 5)
- Daily coaching cron jobs run at 08:00, 13:00, and 18:00 UTC.
- Alert automation:
  - Insulin score > 70 → push: `High carb load detected. 20 min walk suggested.`
  - Protein < 80g → push: `HDL support compromised.`
- Notification settings supports toggles for WhatsApp, push, email, and silent mode.

Implementation details and OpenClaw integration notes are documented in `docs/openclaw_notification_layer.md`.


## Production deployment (Phase 11)
Use the unified setup entry point:
```bash
APP_DOMAIN=yourdomain.com ./setup.sh --prod
```

(Equivalent advanced flow: `./scripts/install_dependencies.sh --prod`, then `./bootstrap.sh --prod`, then `./deploy.sh --prod`.)

Artifacts:
- `scripts/install_dependencies.sh` (dependency installer)
- `deploy.sh` (provisioning + deployment)
- `update.sh` (rebuild/restart + health checks)
- `uninstall.sh` (teardown)
- `docs/production_deployment.md` (architecture diagram + operations)

## Dev run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Migrations
Manual SQL migration scripts are in `migrations/`.

## Example payload: Apple Health sync
```json
{
  "user_id": 1,
  "health_export": {
    "recorded_at": "2026-01-02T08:00:00",
    "steps": 8942,
    "resting_heart_rate": 72,
    "sleep_hours": 6.8,
    "hrv": 52,
    "vo2_max": 41.3,
    "workouts": [
      {
        "exercise_category": "WALK",
        "movement_type": "post_meal_walk",
        "activity_type": "Post Meal Walk",
        "duration_minutes": 22,
        "perceived_intensity": 4,
        "step_count": 2200,
        "calories_estimate": 125,
        "within_60_min_meal": true,
        "performed_at": "2026-01-02T09:00:00Z"
      }
    ]
  }
}
```

Token security: `/apple-sync` requires `Authorization: Bearer <token>` from `POST /auth/token` and enforces token user ↔ payload user matching (admins exempt).

## Example profile configuration
```json
{
  "protein_target_min": 90,
  "protein_target_max": 110,
  "carb_ceiling": 90,
  "oil_limit_tsp": 3,
  "fasting_start_time": "14:00",
  "fasting_end_time": "08:00",
  "max_chapati_per_day": 2,
  "allow_rice": false,
  "chocolate_limit_per_day": 2,
  "insulin_score_green_threshold": 40,
  "insulin_score_yellow_threshold": 70
}
```

## Example exercise log
```json
{
  "user_id": 1,
  "activity_type": "Monkey Bar Session",
  "exercise_category": "MONKEY_BAR",
  "movement_type": "pullups",
  "sets": 4,
  "reps": 6,
  "duration_minutes": 20,
  "perceived_intensity": 8,
  "calories_estimate": 150,
  "post_meal_walk": false
}
```

## Phase 2 Frontend (Next.js)
A mobile-first PWA dashboard is available under `frontend/`.

### Frontend run
```bash
cd frontend
npm install
npm run dev
```

Set backend URL if needed:
```bash
export NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```


## Phase 12 (Monitoring, Backup, Security, Documentation)
- Structured JSON logging with rotating log files.
- Prometheus metrics endpoint: `GET /metrics`.
- Health endpoint includes DB status: `GET /health`.
- Rate limiting + input sanitization middleware.
- JWT auth token endpoint with expiration: `POST /auth/token`.
- Admin-only endpoints (e.g. `GET /admin/system-status`, `GET /metabolic-advisor-report`).
- LLM usage throttling per user (`LLM_REQUESTS_PER_HOUR`).
- Image upload size limit enforcement for food image analysis.
- Backup tooling: `backup.sh`, `restore.sh`, `setup_backup_cron.sh`.
- Additional operational documentation under `docs/`.


## Deterministic deployment (HTTP dev + HTTPS prod)

Use the new environment-aware setup scripts:

```bash
./setup-http.sh
```

This script configures `ENV=development`, sets HTTP-safe cookies/CORS defaults, generates missing secrets, rebuilds containers from scratch, and waits for `GET /health`.

For production with TLS:

```bash
APP_DOMAIN=yourdomain.com LETSENCRYPT_EMAIL=you@example.com ./setup-https.sh
```

This script configures `ENV=production`, enforces HTTPS in the API, sets secure cookie flags, provisions Nginx reverse proxy + Let's Encrypt, and verifies `https://<domain>/health`.

### Migration safety guarantees
- Alembic model metadata is explicitly registered in `alembic/env.py`.
- Container startup runs `alembic upgrade head` with guarded stamp-recovery fallback.
- Non-production startup warns when DB revision differs from repository head.
- No manual migration commands are required for fresh or repeat deploys.
