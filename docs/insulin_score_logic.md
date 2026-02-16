# Insulin Score Logic

Insulin score combines meal-level and daily-level nutritional risk signals.

## Inputs
- Carbohydrate grams
- Hidden oil intake (tsp)
- Fruit sugar grams (weighted)
- Protein intake (protective component)
- Nut HDL support score (protective component)
- Post-meal walk bonus

## Processing
1. Meal macros are aggregated from food logs and image-derived entries.
2. Deterministic scoring computes a raw score and normalized insulin load score.
3. Formula:

```text
InsulinLoadScore =
    (TotalCarbs * 1.0)
  + (HiddenOilEstimate * 0.5)
  + (FruitSugarGrams * 0.8)
  - (ProteinGrams * 0.3)
  - (NutHealthyFatScore * 0.2)
  - (PostMealWalkBonus * 10)
```

4. Profile thresholds classify score zones:
   - Green: below `insulin_score_green_threshold`
   - Yellow: between green/yellow thresholds
   - Red: above `insulin_score_yellow_threshold`

## Enforcement hooks
- Fasting-window violation blocks meal approval.
- Daily carb/oil overages trigger rejection and coaching adjustments.
- High triglycerides (>300) ban banana and mango during reset logging.
- Notifications are emitted for high-risk scores.
