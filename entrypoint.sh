#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=/app

python - <<'PY'
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core.config import settings

engine = create_engine(settings.database_url, future=True)
for attempt in range(60):
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database is ready")
        break
    except OperationalError:
        if attempt == 59:
            raise
        time.sleep(2)
PY

echo "Running alembic migrations"
alembic upgrade head

echo "Starting API server"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
