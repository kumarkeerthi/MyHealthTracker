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
if ! alembic upgrade head; then
  echo "Alembic upgrade failed — attempting auto-stamp recovery"
  python - <<'PY'
from sqlalchemy import create_engine, inspect, text
from app.core.config import settings

engine = create_engine(settings.database_url, future=True)
with engine.connect() as connection:
    inspector = inspect(connection)
    if "alembic_version" not in inspector.get_table_names():
        print("alembic_version table missing; stamping base")
        connection.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"))
        connection.commit()
    rows = connection.execute(text("SELECT version_num FROM alembic_version")).fetchall()
    print(f"Existing alembic_version rows: {rows}")
PY

  alembic stamp base || true
  alembic stamp head
fi

echo "Starting API server"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
