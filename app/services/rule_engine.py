from datetime import datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyLog, ExerciseEntry, MetabolicProfile, User, VitalsEntry
from app.services.exercise_engine import calculate_post_meal_walk_bonus
from app.services.insulin_engine import calculate_insulin_load_score, classify_insulin_score
from app.services.vitals_engine import calculate_vitals_risk_score


def calculate_daily_macros(meal_entries: list[dict]) -> dict[str, float]:
    totals = {"protein": 0.0, "carbs": 0.0, "fats": 0.0, "sugar": 0.0, "fiber": 0.0, "hdl_support": 0.0, "triglyceride_risk": 0.0, "hidden_oil": 0.0}
    for entry in meal_entries:
        servings = entry.get("servings", 1.0)
        totals["protein"] += entry["protein"] * servings
        totals["carbs"] += entry["carbs"] * servings
        totals["fats"] += entry["fats"] * servings
        totals["sugar"] += entry.get("sugar", 0.0) * servings
        totals["fiber"] += entry.get("fiber", 0.0) * servings
        totals["hdl_support"] += entry.get("hdl_support_score", 0.0) * servings
        totals["triglyceride_risk"] += entry.get("triglyceride_risk_weight", 0.0) * servings
        totals["hidden_oil"] += entry["hidden_oil_estimate"] * servings
    return {k: round(v, 2) for k, v in totals.items()}


def get_or_create_metabolic_profile(db: Session, user: User) -> MetabolicProfile:
    profile = db.scalar(select(MetabolicProfile).where(MetabolicProfile.user_id == user.id))
    if profile:
        return profile

    profile = MetabolicProfile(
        user_id=user.id,
        protein_target_min=90,
        protein_target_max=110,
        carb_ceiling=90,
        oil_limit_tsp=3,
        fasting_start_time="14:00",
        fasting_end_time="08:00",
        max_chapati_per_day=2,
        allow_rice=False,
        chocolate_limit_per_day=2,
        insulin_score_green_threshold=40,
        insulin_score_yellow_threshold=70,
    )
    db.add(profile)
    db.flush()
    return profile


def validate_fasting_window(consumed_at: datetime, fasting_start_time: str, fasting_end_time: str) -> bool:
    fasting_start = time.fromisoformat(fasting_start_time)
    fasting_end = time.fromisoformat(fasting_end_time)
    consumed_time = consumed_at.time()

    if fasting_start <= fasting_end:
        in_fasting_window = fasting_start <= consumed_time <= fasting_end
    else:
        in_fasting_window = consumed_time >= fasting_start or consumed_time <= fasting_end

    return not in_fasting_window


def validate_carb_limit(total_carbs: float, carb_ceiling: float) -> bool:
    return total_carbs <= carb_ceiling


def validate_oil_limit(total_hidden_oil: float, oil_limit_tsp: float) -> bool:
    return total_hidden_oil <= oil_limit_tsp


def validate_protein_minimum(total_protein: float, protein_min: float) -> bool:
    return total_protein >= protein_min


def calculate_insulin_load_reduction_bonus(daily_log: DailyLog, exercise_entries: list[ExerciseEntry]) -> float:
    if not daily_log.meal_entries:
        return 0.0

    bonus = 0.0
    for meal in daily_log.meal_entries:
        for exercise in exercise_entries:
            delta_seconds = (exercise.performed_at - meal.consumed_at).total_seconds()
            if 0 <= delta_seconds <= 3600:
                bonus += 1.25
                break
    return bonus


def evaluate_daily_status(db: Session, daily_log: DailyLog, profile: MetabolicProfile) -> dict:
    daily_exercises = db.scalars(select(ExerciseEntry).where(ExerciseEntry.daily_log_id == daily_log.id)).all()
    walk_bonus = calculate_post_meal_walk_bonus(daily_exercises)
    insulin_load_reduction_bonus = calculate_insulin_load_reduction_bonus(daily_log, daily_exercises)
    metabolic_bonus = walk_bonus + insulin_load_reduction_bonus

    insulin_score, raw_score = calculate_insulin_load_score(
        daily_log.total_carbs,
        daily_log.total_hidden_oil,
        daily_log.total_protein,
        metabolic_bonus,
        daily_log.total_sugar,
        daily_log.total_hdl_support,
    )

    vitals_entries = db.scalars(
        select(VitalsEntry)
        .where(VitalsEntry.user_id == daily_log.user_id)
        .order_by(VitalsEntry.recorded_at.asc())
    ).all()
    vitals_risk = calculate_vitals_risk_score(vitals_entries)

    return {
        "insulin_load_score": insulin_score,
        "insulin_load_raw_score": raw_score,
        "insulin_status": classify_insulin_score(insulin_score, profile),
        "protein_compliance": validate_protein_minimum(daily_log.total_protein, profile.protein_target_min),
        "carb_compliance": validate_carb_limit(daily_log.total_carbs, profile.carb_ceiling),
        "oil_compliance": validate_oil_limit(daily_log.total_hidden_oil, profile.oil_limit_tsp),
        "fasting_compliance": True,
        "vitals_risk_flag": vitals_risk["flag"],
        "insulin_load_reduction_bonus": insulin_load_reduction_bonus,
    }
