from app.models import MetabolicProfile


POST_MEAL_WALK_BONUS = 10
DINNER_CARB_LIMIT_GRAMS = 30
DINNER_INSULIN_PENALTY_MULTIPLIER = 1.2
LATE_DINNER_PENALTY = 4.0
PROTEIN_ONLY_DINNER_BONUS = 2.5


def calculate_insulin_load_score(
    total_carbs: float,
    hidden_oil_estimate: float,
    protein_grams: float,
    post_meal_walk_bonus: float,
    fruit_sugar_grams: float = 0.0,
    nut_healthy_fat_score: float = 0.0,
) -> tuple[float, float]:
    fruit_sugar_weight = fruit_sugar_grams * 0.8
    nut_hdl_bonus = nut_healthy_fat_score * 0.2
    raw_score = (
        (total_carbs * 1.0)
        + (hidden_oil_estimate * 0.5)
        + fruit_sugar_weight
        - (protein_grams * 0.3)
        - nut_hdl_bonus
        - (post_meal_walk_bonus * POST_MEAL_WALK_BONUS)
    )
    normalized = max(0.0, min(100.0, round(raw_score, 2)))
    return normalized, round(raw_score, 2)


def calculate_dinner_adjustment(
    dinner_carbs: float,
    dinner_protein: float,
    dinner_mode: str | None = None,
    dinner_logged_after_20: bool = False,
) -> dict[str, float | bool | str]:
    mode = (dinner_mode or "standard").lower()
    protein_only_mode = mode == "protein_only" or (dinner_carbs <= 5 and dinner_protein >= 20)
    low_carb_mode = mode == "low_carb"

    carb_over_limit = max(0.0, dinner_carbs - DINNER_CARB_LIMIT_GRAMS)
    base_penalty = dinner_carbs * 0.5
    scaled_penalty = base_penalty * DINNER_INSULIN_PENALTY_MULTIPLIER
    over_limit_penalty = carb_over_limit * 0.75
    time_penalty = LATE_DINNER_PENALTY if dinner_logged_after_20 else 0.0
    protein_bonus = PROTEIN_ONLY_DINNER_BONUS if protein_only_mode else 0.0

    impact = round(max(0.0, scaled_penalty + over_limit_penalty + time_penalty - protein_bonus), 2)

    return {
        "impact": impact,
        "carb_limit_exceeded": carb_over_limit > 0,
        "evening_spike_risk": carb_over_limit > 0,
        "protein_only_bonus_applied": protein_only_mode,
        "late_dinner_penalty_applied": dinner_logged_after_20,
        "mode": "protein_only" if protein_only_mode else "low_carb" if low_carb_mode else "standard",
    }


def classify_insulin_score(score: float, profile: MetabolicProfile) -> str:
    if score <= profile.insulin_score_green_threshold:
        return "green"
    if score <= profile.insulin_score_yellow_threshold:
        return "yellow"
    return "red"
