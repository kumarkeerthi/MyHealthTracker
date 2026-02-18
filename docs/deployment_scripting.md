# Deployment Scripting

This document captures the current deployment entrypoint behavior and migration guarantees.

## Entrypoint behavior

The container entrypoint now follows a strict startup sequence:

1. Wait for the database connection to become available.
2. Run `alembic upgrade head` exactly once.
3. If migrations fail, the container exits with a non-zero status.
4. Start the API process only after migrations succeed.

There is no automatic `alembic stamp` fallback anymore. This avoids hidden schema drift and makes deployment failures explicit.

## Operational implications

- Every release must ship valid Alembic migrations.
- Schema problems fail fast during startup rather than being masked.
- Rollback and forward-fix procedures should be managed through migration scripts, not runtime auto-repair logic.

## Local and production parity

The same migration-first boot flow applies in development and production. This keeps deployment behavior predictable across environments.
