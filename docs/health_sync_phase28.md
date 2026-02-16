# Phase 28 — Secure Health Data Sync Architecture

This phase documents the secure iOS-to-backend health summary synchronization model focused on integrity, anti-replay protections, and deterministic merge behavior.

## Design goals

- Accept daily health summaries without requiring raw HealthKit exports.
- Ensure payload authenticity and freshness.
- Prevent duplicate/replayed sync writes.
- Merge updates safely when data arrives incrementally.

## Example payload

```json
{
  "date": "2026-02-16",
  "steps": 9234,
  "resting_hr": 58,
  "sleep_hours": 7.4,
  "hrv": 46.2,
  "workouts": [
    {
      "type": "running",
      "duration": 42,
      "calories": 418.5,
      "start_time": "2026-02-16T06:22:00Z"
    }
  ],
  "generated_at": "2026-02-16T23:59:45Z"
}
```

## Security envelope

Typical request includes:

- `Authorization: Bearer <jwt>`
- `X-Sync-Timestamp: <unix-or-iso timestamp>`
- `X-Sync-Signature: <hmac_sha256(timestamp + '.' + body)>`

Backend verifies:
1. JWT validity and user scope.
2. Signature correctness using shared secret.
3. Timestamp freshness within replay window.
4. Request rate limits (per user and/or global).

## Sync sequence (textual)

1. iOS HealthKit manager aggregates per-day summary data.
2. Sync manager signs payload and sends request with timestamp/signature headers.
3. Backend authenticates request and validates anti-replay controls.
4. Input bounds checks reject implausible values (steps, HR, sleep, workout metrics).
5. Backend resolves target row by `(user_id, date)`.
6. If row exists, merge strategy compares `generated_at` and deduplicates workouts via stable key (`type + start_time`).
7. Backend writes result (`created`, `merged`, or `unchanged`) and logs sync metadata.

## Merge strategy guidelines

- Newer `generated_at` generally wins for scalar daily summaries.
- Missing fields in existing rows can be backfilled from incoming payload.
- Workout list merges should avoid duplicates and preserve earliest provenance metadata.
- Idempotent re-submissions should produce `unchanged` when no delta exists.

## Validation and limits

Recommended validation rules:

- Steps: non-negative and below configured upper bound.
- Resting HR: physiological range check.
- Sleep hours: bounded daily plausible window.
- Workout duration/calories: reject clearly absurd outliers.

## Operational logging

Capture at minimum:

- user id
- payload byte size
- sync timestamp received
- verification result (pass/fail reason)
- write result (`created`/`merged`/`unchanged`)
- processing latency

## Failure handling expectations

- **Invalid signature** → reject with auth/integrity error.
- **Stale timestamp** → reject as replay risk.
- **Schema/bounds invalid** → reject with validation details.
- **Transient backend failure** → return retryable error; client should backoff and retry.
