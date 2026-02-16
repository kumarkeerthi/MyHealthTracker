# Phase 28 — Secure Health Data Sync Architecture

## Example JSON payload

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

## Sync sequence diagram (textual)

1. iOS HealthKit manager aggregates daily summaries only (no raw HealthKit export).
2. Sync manager signs `timestamp.body` with HMAC SHA-256 and includes `X-Sync-Timestamp` + `X-Sync-Signature` headers.
3. Backend route verifies JWT auth, validates signature, enforces replay-window freshness, and applies user/hour rate limits.
4. Backend validates bounds (steps, HR, sleep, workout values) and rejects absurd values.
5. Backend checks for an existing row for `(user_id, date)`.
6. If row exists, it compares `generated_at` timestamps, merges with deduplicated workouts (`type + start_time`), and updates only when newer or missing data is provided.
7. Backend logs sync time, payload size, and result (`created`, `merged`, or `unchanged`).
