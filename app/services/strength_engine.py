from datetime import datetime, timedelta

from app.models import ExerciseCategory, ExerciseEntry


def _safe_max(values: list[int | None]) -> int:
    usable = [v for v in values if v is not None]
    return max(usable) if usable else 0


def compute_monkey_bar_progress(entries: list[ExerciseEntry]) -> dict[str, int]:
    monkey = [entry for entry in entries if entry.exercise_category == ExerciseCategory.MONKEY_BAR]
    return {
        "dead_hang_duration_seconds": _safe_max([entry.dead_hang_duration_seconds for entry in monkey]),
        "pull_up_count": _safe_max([entry.pull_up_count for entry in monkey]),
        "assisted_pull_up_reps": _safe_max([entry.assisted_pull_up_reps for entry in monkey]),
        "grip_endurance_seconds": _safe_max([entry.grip_endurance_seconds for entry in monkey]),
    }


def _exercise_reps_total(entries: list[ExerciseEntry], movement_names: set[str]) -> int:
    return sum((entry.reps or 0) * (entry.sets or 1) for entry in entries if entry.movement_type in movement_names)


def compute_strength_score(entries: list[ExerciseEntry]) -> dict[str, float | int]:
    pushups = _exercise_reps_total(entries, {"pushups"})
    pullups = sum(entry.pull_up_count or 0 for entry in entries)
    squats = _exercise_reps_total(entries, {"squats"})
    dead_hang_seconds = sum(entry.dead_hang_duration_seconds or 0 for entry in entries)

    strength_index = round((pushups * 0.25) + (pullups * 2.0) + (dead_hang_seconds * 0.08) + (squats * 0.2), 2)
    return {
        "pushups": pushups,
        "pullups": pullups,
        "dead_hang_seconds": dead_hang_seconds,
        "squats": squats,
        "strength_index": strength_index,
    }


def compute_weekly_strength_graph(entries: list[ExerciseEntry], now: datetime | None = None) -> list[float]:
    ref = now or datetime.utcnow()
    series: list[float] = []
    for offset in range(6, -1, -1):
        day = (ref - timedelta(days=offset)).date()
        day_entries = [entry for entry in entries if entry.performed_at.date() == day]
        series.append(float(compute_strength_score(day_entries)["strength_index"]))
    return series


def compute_grip_improvement_percent(entries: list[ExerciseEntry], now: datetime | None = None) -> float:
    ref = now or datetime.utcnow()
    last_7_start = ref - timedelta(days=7)
    prev_7_start = ref - timedelta(days=14)

    recent = [entry for entry in entries if entry.performed_at >= last_7_start]
    previous = [entry for entry in entries if prev_7_start <= entry.performed_at < last_7_start]

    recent_grip = sum(entry.grip_endurance_seconds or 0 for entry in recent)
    previous_grip = sum(entry.grip_endurance_seconds or 0 for entry in previous)

    if previous_grip <= 0:
        return 100.0 if recent_grip > 0 else 0.0

    return round(((recent_grip - previous_grip) / previous_grip) * 100, 2)


def metabolic_strength_signals(entries: list[ExerciseEntry], now: datetime | None = None) -> dict[str, bool | str]:
    ref = now or datetime.utcnow()
    week_start = ref - timedelta(days=7)
    prev_week_start = ref - timedelta(days=14)
    prev_prev_week_start = ref - timedelta(days=21)

    this_week_strength = [
        entry for entry in entries if entry.exercise_category in {ExerciseCategory.STRENGTH, ExerciseCategory.BODYWEIGHT, ExerciseCategory.MONKEY_BAR} and entry.performed_at >= week_start
    ]
    prev_week_strength = [
        entry
        for entry in entries
        if entry.exercise_category in {ExerciseCategory.STRENGTH, ExerciseCategory.BODYWEIGHT, ExerciseCategory.MONKEY_BAR}
        and prev_week_start <= entry.performed_at < week_start
    ]
    prev_prev_week_strength = [
        entry
        for entry in entries
        if entry.exercise_category in {ExerciseCategory.STRENGTH, ExerciseCategory.BODYWEIGHT, ExerciseCategory.MONKEY_BAR}
        and prev_prev_week_start <= entry.performed_at < prev_week_start
    ]

    hdl_improvement_mode = len(this_week_strength) >= 3

    prev_week_score = float(compute_strength_score(prev_week_strength)["strength_index"])
    prev_prev_week_score = float(compute_strength_score(prev_prev_week_strength)["strength_index"])
    this_week_score = float(compute_strength_score(this_week_strength)["strength_index"])

    muscle_stimulus_reduced = prev_prev_week_score > prev_week_score > this_week_score and prev_prev_week_score > 0

    metabolic_message = "Strength momentum stable"
    if hdl_improvement_mode:
        metabolic_message = "HDL Improvement Mode"
    elif muscle_stimulus_reduced:
        metabolic_message = "Muscle Stimulus Reduced"

    return {
        "hdl_improvement_mode": hdl_improvement_mode,
        "muscle_stimulus_reduced": muscle_stimulus_reduced,
        "metabolic_message": metabolic_message,
    }
