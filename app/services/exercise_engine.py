from collections.abc import Iterable

from app.models import ExerciseCategory, ExerciseEntry

SUPPORTED_MOVEMENTS: dict[ExerciseCategory, set[str]] = {
    ExerciseCategory.BODYWEIGHT: {"pushups", "squats", "plank", "lunges"},
    ExerciseCategory.MONKEY_BAR: {
        "dead_hang",
        "pullups",
        "assisted_pullups",
        "grip_hold",
        "hanging_knee_raise",
    },
    ExerciseCategory.WALK: {"post_meal_walk", "outdoor_walk", "indoor_walk"},
}


def is_supported_movement(category: ExerciseCategory, movement_type: str) -> bool:
    allowed = SUPPORTED_MOVEMENTS.get(category)
    if not allowed:
        return True
    return movement_type in allowed


def infer_workout_category(activity_type: str, movement_type: str) -> ExerciseCategory:
    normalized = f"{activity_type} {movement_type}".lower()
    if "walk" in normalized:
        return ExerciseCategory.WALK
    if any(token in normalized for token in ["pull", "hang", "grip", "monkey"]):
        return ExerciseCategory.MONKEY_BAR
    if any(token in normalized for token in ["push", "squat", "bodyweight"]):
        return ExerciseCategory.BODYWEIGHT
    return ExerciseCategory.STRENGTH


def calculate_post_meal_walk_bonus(entries: Iterable[ExerciseEntry]) -> float:
    bonus = 0.0
    for entry in entries:
        is_walk = entry.exercise_category == ExerciseCategory.WALK
        if (entry.post_meal_walk or is_walk) and entry.duration_minutes >= 15:
            bonus += 1
    return bonus
