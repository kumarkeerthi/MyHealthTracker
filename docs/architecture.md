# Architecture Overview

This project follows a **backend-first modular architecture** designed for deterministic metabolic analytics, event-driven coaching, and multi-client support (web + iOS).

## System components

- **FastAPI backend (`app/`)**
  - Hosts REST APIs, validation, deterministic rule engines, security middleware, schedulers, and orchestration logic.
- **PostgreSQL**
  - System of record for users, food logs, vitals, exercises, profiles, advisor outputs, and audit-friendly events.
- **Redis + Celery**
  - Supports asynchronous/background workloads where immediate request-response execution is not ideal.
- **Next.js frontend (`frontend/`)**
  - Mobile-first dashboard and PWA shell for day-to-day user interaction.
- **iOS SwiftUI client (`ios/`)**
  - Native app path with HealthKit sync, authentication, and push-related flows.

## Backend runtime flow

1. **Ingress & middleware**
   - CORS, HTTPS enforcement, security headers, CSRF checks, input sanitization, auth enforcement, and rate limiting are applied early in request handling.
2. **Routing layer**
   - Route modules parse payloads and map requests to service functions.
3. **Service layer**
   - Business logic (e.g., insulin scoring, exercise analysis, hydration, notifications, advisor recommendations).
4. **Persistence layer**
   - SQLAlchemy model/session lifecycle and database transactions.
5. **Observability hooks**
   - Structured logs, health probes, metrics counters/timers.

## Service modules worth knowing

- `app/services/insulin_engine.py` — insulin-impact scoring logic.
- `app/services/exercise_engine.py` + `movement_engine.py` + `strength_engine.py` — movement quality, classification, and progression metrics.
- `app/services/food_image_service.py` — image-assisted food interpretation pipeline.
- `app/services/apple_health_service.py` — Health data import/sync normalization.
- `app/services/coaching_scheduler.py` + `metabolic_advisor_scheduler.py` — time-based recommendation generation.
- `app/services/notification_service.py` + `push_service.py` — outbound notification orchestration.

## Data model strategy

- Schema evolves through SQL migration scripts in `migrations/`.
- Startup path creates metadata and seeds baseline profile/configuration records.
- API schemas in `app/schemas/schemas.py` enforce payload consistency before business logic runs.

## Deployment topology

Primary deployment wiring is in `docker-compose.prod.yml` with containers for:
- backend
- frontend
- postgres
- redis
- celery worker
- nginx reverse proxy
- watchdog/alert utility

Use `deploy.sh` for guided provisioning and `update.sh` for rolling updates.

## Observability and operational controls

- `GET /health` for service + DB health probes.
- `GET /metrics` for Prometheus-compatible scraping.
- JSON-structured rotating logs configured from `app/core/logging_config.py`.
- Container healthchecks and optional alert webhook (`deploy/container_alert.sh`).

## Architectural principles

- **Determinism before ML**: AI outputs are useful, but deterministic guardrails remain source of truth for safety-critical checks.
- **Defense in depth**: auth, sanitization, rate limiting, and transport/security headers are layered.
- **Operationally explicit**: backup/restore, deploy/update, monitoring, and security docs are first-class.
- **Client parity**: backend contracts are designed to serve web and native clients without drift.
