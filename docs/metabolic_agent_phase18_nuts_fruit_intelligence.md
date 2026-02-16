# Phase 18: Nuts & Fruit Intelligence Layer

## Example `POST /log-food` response

```json
{
  "daily_log_id": 42,
  "log_date": "2026-02-16",
  "total_protein": 97.4,
  "total_carbs": 62.1,
  "total_fats": 39.5,
  "total_sugar": 14.2,
  "total_fiber": 18.6,
  "total_hidden_oil": 2.1,
  "insulin_load_score": 31.7,
  "fruit_servings": 1.0,
  "fruit_budget": 1.0,
  "nuts_servings": 1.0,
  "nuts_budget": 1.0,
  "remaining_carb_budget": 27.9,
  "suggestions": [
    "Pair fruit with protein.",
    "Healthy fat – supports HDL."
  ],
  "warnings": [],
  "validations": {
    "carb_limit": true,
    "oil_limit": true,
    "protein_minimum": true
  }
}
```

## Example `GET /daily-summary` response

```json
{
  "date": "2026-02-16",
  "total_protein": 97.4,
  "total_carbs": 62.1,
  "total_fats": 39.5,
  "total_sugar": 14.2,
  "total_fiber": 18.6,
  "total_hidden_oil": 2.1,
  "insulin_load_score": 31.7,
  "fruit_servings": 1.0,
  "fruit_budget": 1.0,
  "nuts_servings": 1.0,
  "nuts_budget": 1.0,
  "remaining_carb_budget": 27.9,
  "warnings": [
    "High insulin fruit for current triglyceride level."
  ],
  "validations": {
    "carb_limit": true,
    "oil_limit": true,
    "protein_minimum": true
  }
}
```

## Example `GET /analytics/advanced` additions

```json
{
  "fruit_frequency_trend": { "key": "fruit_frequency", "trend": "steady", "points": [] },
  "nut_frequency_trend": { "key": "nut_frequency", "trend": "improvement", "points": [] },
  "sugar_load_trend": { "key": "sugar_load_trend", "trend": "improvement", "points": [] },
  "hdl_support_trend": { "key": "hdl-support_trend", "trend": "improvement", "points": [] }
}
```
