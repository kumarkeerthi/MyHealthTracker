# Phase 16: Advanced Adaptive Metabolic Optimization Agent

## Agent architecture
- New service module: `app/services/metabolic_agent.py`.
- Deterministic analysis engine with 3 run cadences:
  - Daily lightweight scan.
  - Weekly deep analysis.
  - Monthly macro-evaluation.
- Safety gate: recommendations are written to `pending_recommendations` and require user Accept/Reject before profile changes.
- Explainability is embedded per recommendation:
  - `data_used`
  - `threshold_triggered`
  - `historical_comparison`
  - `confidence_level`
- Optional LLM layer is summarization-only and never rule-generating.

## Scheduled tasks (Celery beat)
- `metabolic_agent.daily_scan`: every day at 04:30 UTC.
- `metabolic_agent.weekly_analysis`: every Monday at 05:00 UTC.
- `metabolic_agent.monthly_review`: day 1 of each month at 05:30 UTC.

## Recommendation logic
### Daily scan
Evaluates:
- Insulin load average over last 3 days.
- Carb ceiling compliance.
- Protein compliance.
- Fasting violations.
- Hydration compliance.
- Strength sessions logged.

Rules:
- If insulin load > 70 for two recent days: recommend "Reduce carb intake tomorrow."
- If protein < 80g for two recent days: recommend "Add whey tomorrow."

### Weekly deep analysis
Evaluates:
- Waist trend (7-day rolling average).
- Strength index trend.
- Resting heart-rate trend.
- Sleep trend.
- Fruit frequency.
- Oil usage pattern.
- Image-detected restaurant frequency.

Rules:
- If waist not reducing AND carb ceiling > 80: recommend reducing carb ceiling by 10g.
- If strength rising AND waist stable: allow 1 controlled refeed meal.
- If HDL-support days are high (nuts + strength): mark HDL support consistent.

### Monthly review
Evaluates:
- Average insulin score.
- Average strength score.
- Waist reduction.
- Habit compliance.
- Fasting compliance.

Output:
- Monthly Metabolic Report with:
  - Risk classification.
  - Suggested carb tolerance phase.
  - Suggested strength progression phase.
  - Suggested hydration improvements.

## Example weekly report JSON
```json
{
  "report_type": "weekly_metabolic_analysis",
  "window": {
    "start": "2026-02-09",
    "end": "2026-02-15"
  },
  "metrics": {
    "waist_recent_avg_cm": 92.1,
    "waist_previous_avg_cm": 92.5,
    "strength_recent_index": 31.2,
    "strength_previous_index": 28.7,
    "resting_hr_recent": 64.8,
    "sleep_recent_hours": 7.1,
    "fruit_days": 2,
    "oil_avg_daily_tsp": 2.4,
    "image_detected_restaurant_frequency": 1
  },
  "recommendation_logic": {
    "carb_reduction_rule": "If waist not reducing AND carb ceiling > 80, recommend -10g carb ceiling (pending approval).",
    "refeed_rule": "If strength rising AND waist stable, allow 1 controlled refeed meal.",
    "hdl_support_rule": "If nuts + strength days are high, mark HDL support consistent."
  }
}
```

## LLM prompt template (summarization-only)
```text
System:
Summarize deterministic weekly metabolic analysis in a motivating tone.
Do not invent rules, thresholds, or recommendations.
Only restate deterministic findings provided in JSON.

User:
<structured_weekly_analysis_json>
```

## Database migrations
- Added `migrations/005_metabolic_agent_state_and_pending_recommendations.sql`.
- New tables:
  - `metabolic_agent_state`
  - `pending_recommendations`
