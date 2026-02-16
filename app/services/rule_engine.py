from datetime import datetime, time


def calculate_daily_macros(meal_entries: list[dict]) -> dict[str, float]:
    totals = {"protein": 0.0, "carbs": 0.0, "fats": 0.0, "hidden_oil": 0.0}
    for entry in meal_entries:
        servings = entry.get("servings", 1.0)
        totals["protein"] += entry["protein"] * servings
        totals["carbs"] += entry["carbs"] * servings
        totals["fats"] += entry["fats"] * servings
        totals["hidden_oil"] += entry["hidden_oil_estimate"] * servings
    return {k: round(v, 2) for k, v in totals.items()}


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
        - (post_meal_walk_bonus * 10)
    )
    normalized = max(0.0, min(100.0, round(raw_score, 2)))
    return normalized, round(raw_score, 2)


def validate_fasting_window(consumed_at: datetime, start: str = "08:00", end: str = "14:00") -> bool:
    start_time = time.fromisoformat(start)
    end_time = time.fromisoformat(end)
    return start_time <= consumed_at.time() <= end_time


def validate_carb_limit(total_carbs: float, carb_ceiling: float = 90.0) -> bool:
    return total_carbs <= carb_ceiling


def validate_oil_limit(total_hidden_oil: float, oil_limit_tsp: float = 3.0) -> bool:
    return total_hidden_oil <= oil_limit_tsp


def validate_protein_minimum(total_protein: float, protein_min: float = 90.0) -> bool:
    return total_protein >= protein_min
