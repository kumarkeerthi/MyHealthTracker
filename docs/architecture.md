# Architecture

MyHealthTracker uses a modular backend-first architecture:

- **FastAPI backend** (`app/`) for APIs, business rules, and scheduling.
- **PostgreSQL** as primary datastore.
- **Redis + Celery** for asynchronous workloads.
- **Next.js frontend** (`frontend/`) for dashboard and PWA experience.
- **Docker Compose** for local and production orchestration.

## Runtime layers
1. **API layer**: request validation + route handlers.
2. **Service layer**: rule engine, LLM advisor, image analysis, coaching scheduler.
3. **Data layer**: SQLAlchemy models and session management.
4. **Ops layer**: metrics, health checks, logging, backups, restore and alerting scripts.

## Observability
- `/health` endpoint with DB probe.
- `/metrics` endpoint for Prometheus scraping.
- Structured JSON logs with rotating log files.
- Container healthchecks and watchdog alert script.
