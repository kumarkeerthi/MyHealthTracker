# Apple Health Integration

Apple Health can be synced automatically using **iOS Shortcuts** with `POST /apple-sync`.

## Recommended approach (Option A): iOS Shortcut relay

### 1) Create API token
1. Call `POST /auth/token?user_id=<id>`.
2. Copy the returned bearer token.
3. Store it in iOS Shortcut as a Text variable (or in a secure vault app + Shortcut import).

### 2) Create daily Shortcut automation
In the iOS Shortcuts app:
1. Create a personal automation (time-based, once daily).
2. Add HealthKit read actions for:
   - Steps (today)
   - Resting Heart Rate
   - Sleep duration
   - HRV
   - VO2 Max (optional)
   - Workouts from last 24h
3. Build JSON payload in this shape:

```json
{
  "user_id": 1,
  "health_export": {
    "recorded_at": "2026-02-15T21:30:00Z",
    "steps": 10534,
    "resting_heart_rate": 63,
    "sleep_hours": 7.4,
    "hrv": 58,
    "vo2_max": 42.1,
    "heart_rate_zones": {
      "zone_1": 42,
      "zone_2": 28,
      "zone_3": 10,
      "zone_4": 0,
      "zone_5": 0
    },
    "workouts": [
      {
        "workout_type": "Walking",
        "activity_type": "Post Meal Walk",
        "movement_type": "outdoor_walk",
        "duration_minutes": 22,
        "step_count": 2200,
        "calories_estimate": 125,
        "performed_at": "2026-02-15T20:20:00Z",
        "within_60_min_meal": true
      }
    ]
  }
}
```

4. Add **Get Contents of URL** action:
   - Method: `POST`
   - URL: `https://<your-host>/apple-sync`
   - Headers:
     - `Authorization: Bearer <token>`
     - `Content-Type: application/json`
   - Body: JSON from step 3.

### 3) Verify sync
- Check API response for `workouts_imported`, `hrv_synced`, and `vo2_max_synced`.
- Use `GET /exercise-summary` and `GET /vitals-summary` to confirm records.

## Data processing behavior
- Vitals table receives: steps, resting HR, sleep, HRV, VO2 max, HR zones.
- Exercise table receives each Apple workout session.
- Walk/workout events are matched against meal timestamps:
  - If exercise occurs within **1 hour after a meal**, insulin reduction bonus is applied during score recomputation.

## Token security guidance
- Use bearer tokens from `/auth/token`.
- Prefer short-lived tokens; rotate periodically.
- Never hardcode production tokens in public Shortcut links.
- Keep Shortcut sharing disabled for automations containing live secrets.

## Option B (background relay service)
A native always-on relay process can be added later, but iOS Shortcut automation is the practical baseline due to Apple HealthKit permission boundaries on iOS.
