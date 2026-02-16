# Metabolic Intelligence Engine (Phase 1+ Extensions)

Clinical-grade metabolic intelligence backend built with FastAPI, SQLAlchemy, and PostgreSQL.

## Features
- Deterministic rule engine for insulin load scoring and nutrition validations.
- Configurable `metabolic_profiles` per user (seeded with defaults).
- Expanded exercise model (`exercise_category`, movement metadata, intensity, steps/calories).
- Expanded vitals model (`resting_hr`, `sleep_hours`, `waist_cm`, `hrv`, `steps_total`, `body_fat_percentage`).
- Apple Health web-friendly ingestion endpoint and service layer.
- New profile, exercise summary, vitals summary, and external-event endpoints.
- WhatsApp webhook, notification event webhook, notification settings API, and automated coaching scheduler.

## Stack
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Docker / Docker Compose

## Run with Docker
```bash
docker compose up --build
```

API available at: `http://localhost:8000`

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
- `POST /import-apple-health`
- `POST /external-event`
- `POST /llm/analyze`
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

## Dev run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Migrations
Manual SQL migration scripts are in `migrations/`.

## Example payload: Apple Health import
```json
{
  "user_id": 1,
  "health_export": {
    "recorded_at": "2026-01-02T08:00:00",
    "steps": 8942,
    "resting_heart_rate": 72,
    "sleep_hours": 6.8,
    "workouts": [
      {
        "exercise_category": "WALK",
        "movement_type": "post_meal_walk",
        "activity_type": "Post Meal Walk",
        "duration_minutes": 22,
        "perceived_intensity": 4,
        "step_count": 2200,
        "calories_estimate": 125
      }
    ]
  }
}
```

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
