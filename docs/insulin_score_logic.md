# Insulin Score Logic

Insulin score combines meal-level and daily-level nutritional risk signals.

## Inputs
- Carbohydrate grams
- Hidden oil intake (tsp)
- Protein intake (protective component)

## Processing
1. Meal macros are aggregated from food logs and image-derived entries.
2. Deterministic scoring computes a raw score and normalized insulin load score.
3. Profile thresholds classify score zones:
   - Green: below `insulin_score_green_threshold`
   - Yellow: between green/yellow thresholds
   - Red: above `insulin_score_yellow_threshold`

## Enforcement hooks
- Fasting-window violation blocks meal approval.
- Daily carb/oil overages trigger rejection and coaching adjustments.
- Notifications are emitted for high-risk scores.
