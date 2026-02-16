# Metabolic Intelligence Engine (Phase 1)

Clinical-grade metabolic intelligence backend built with FastAPI, SQLAlchemy, and PostgreSQL.

## Features
- Deterministic rule engine for insulin load scoring and nutrition validations.
- Core APIs to log food, vitals, exercise, and generate daily/weekly summaries.
- PostgreSQL-backed schema for users, food catalog, meal logs, vitals, exercise, and insulin scores.
- Startup seed with hardcoded user profile + required food items.

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
- `POST /log-food`
- `GET /daily-summary`
- `POST /log-vitals`
- `POST /log-exercise`
- `GET /weekly-summary`
- `GET /health`

## Dev run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Rule Engine
`app/services/rule_engine.py`

InsulinLoadScore:
```
(TotalCarbs * 1.0)
+ (HiddenOilEstimate * 0.5)
- (ProteinGrams * 0.3)
- (PostMealWalkBonus * 10)
```
Normalized to 0–100 via clamping.
