# Metabolic Intelligence Engine (Phase 1+ Extensions)

Clinical-grade metabolic intelligence backend built with FastAPI, SQLAlchemy, and PostgreSQL.

## Features
- Deterministic rule engine for insulin load scoring and nutrition validations.
- Configurable `metabolic_profiles` per user (seeded with defaults).
- Expanded exercise model (`exercise_category`, movement metadata, intensity, steps/calories).
- Expanded vitals model (`resting_hr`, `sleep_hours`, `waist_cm`, `hrv`, `steps_total`, `body_fat_percentage`).
- Apple Health web-friendly ingestion endpoint and service layer.
- New profile, exercise summary, vitals summary, and external-event endpoints.

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
