from app.models import MetabolicProfile


POST_MEAL_WALK_BONUS = 10


def calculate_insulin_load_score(
    total_carbs: float,
    hidden_oil_estimate: float,
    protein_grams: float,
    post_meal_walk_bonus: float,
) -> tuple[float, float]:
    raw_score = (
        (total_carbs * 1.0)
        + (hidden_oil_estimate * 0.5)
        - (protein_grams * 0.3)
        - (post_meal_walk_bonus * POST_MEAL_WALK_BONUS)
    )
    normalized = max(0.0, min(100.0, round(raw_score, 2)))
    return normalized, round(raw_score, 2)


def classify_insulin_score(score: float, profile: MetabolicProfile) -> str:
    if score <= profile.insulin_score_green_threshold:
        return "green"
    if score <= profile.insulin_score_yellow_threshold:
        return "yellow"
    return "red"
