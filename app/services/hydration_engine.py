from app.models import DailyLog

HYDRATION_TARGET_MIN_ML = 2500
HYDRATION_TARGET_MAX_ML = 3000


def hydration_score(water_ml: int) -> float:
    return round(min(100.0, (water_ml / HYDRATION_TARGET_MIN_ML) * 100), 1)


def hydration_status_message(water_ml: int) -> str:
    if water_ml >= HYDRATION_TARGET_MIN_ML:
        return "Hydration target achieved."
    if water_ml < 1200:
        return "Recovery Mode: water intake below pace."
    return "Discipline Active: keep hydrating toward target."


def apply_hydration_update(daily_log: DailyLog, amount_ml: int):
    daily_log.water_ml = int((daily_log.water_ml or 0) + amount_ml)
    daily_log.hydration_score = hydration_score(daily_log.water_ml)
    return {
        "water_ml": daily_log.water_ml,
        "hydration_score": daily_log.hydration_score,
        "hydration_target_min_ml": HYDRATION_TARGET_MIN_ML,
        "hydration_target_max_ml": HYDRATION_TARGET_MAX_ML,
        "hydration_target_achieved": daily_log.water_ml >= HYDRATION_TARGET_MIN_ML,
        "message": hydration_status_message(daily_log.water_ml),
    }
