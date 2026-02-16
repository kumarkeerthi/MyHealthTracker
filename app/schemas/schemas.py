from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.models import ExerciseCategory


class MealEntryInput(BaseModel):
    food_item_id: int
    servings: float = Field(default=1.0, gt=0)


class LogFoodRequest(BaseModel):
    user_id: int = 1
    consumed_at: datetime
    entries: list[MealEntryInput]


class LogFoodResponse(BaseModel):
    daily_log_id: int
    log_date: date
    total_protein: float
    total_carbs: float
    total_fats: float
    total_hidden_oil: float
    insulin_load_score: float
    validations: dict[str, bool]


class LogVitalsRequest(BaseModel):
    user_id: int = 1
    recorded_at: datetime | None = None
    weight_kg: float | None = None
    fasting_glucose: float | None = None
    hba1c: float | None = None
    triglycerides: float | None = None
    hdl: float | None = None
    resting_hr: float | None = None
    sleep_hours: float | None = None
    waist_cm: float | None = None
    hrv: float | None = None
    steps_total: int = 0
    body_fat_percentage: float | None = None


class LogExerciseRequest(BaseModel):
    user_id: int = 1
    activity_type: str
    exercise_category: ExerciseCategory = ExerciseCategory.STRENGTH
    movement_type: str = "general"
    reps: int | None = None
    sets: int | None = None
    duration_minutes: int = Field(gt=0)
    perceived_intensity: int = Field(default=5, ge=1, le=10)
    step_count: int | None = None
    calories_estimate: float | None = None
    calories_burned_estimate: float = 0.0
    post_meal_walk: bool = False
    performed_at: datetime | None = None


class ProfileResponse(BaseModel):
    user_id: int
    protein_target_min: int
    protein_target_max: int
    carb_ceiling: int
    oil_limit_tsp: float
    fasting_start_time: str
    fasting_end_time: str
    max_chapati_per_day: int
    allow_rice: bool
    chocolate_limit_per_day: int
    insulin_score_green_threshold: float
    insulin_score_yellow_threshold: float


class UpdateProfileRequest(BaseModel):
    protein_target_min: int | None = None
    protein_target_max: int | None = None
    carb_ceiling: int | None = None
    oil_limit_tsp: float | None = None
    fasting_start_time: str | None = None
    fasting_end_time: str | None = None
    max_chapati_per_day: int | None = None
    allow_rice: bool | None = None
    chocolate_limit_per_day: int | None = None
    insulin_score_green_threshold: float | None = None
    insulin_score_yellow_threshold: float | None = None

    @field_validator("fasting_start_time", "fasting_end_time")
    @classmethod
    def validate_time(cls, value: str | None):
        if value is None:
            return value
        datetime.strptime(value, "%H:%M")
        return value


class DailySummaryResponse(BaseModel):
    date: date
    total_protein: float
    total_carbs: float
    total_fats: float
    total_hidden_oil: float
    insulin_load_score: float | None
    validations: dict[str, bool]


class WeeklySummaryResponse(BaseModel):
    days_logged: int
    avg_protein: float
    avg_carbs: float
    avg_fats: float
    avg_hidden_oil: float
    avg_insulin_load_score: float


class AppleHealthImportRequest(BaseModel):
    user_id: int = 1
    health_export: dict | None = None
    relay: dict | None = None


class ExerciseSummaryResponse(BaseModel):
    user_id: int
    total_sessions: int
    total_duration_minutes: int
    total_steps: int


class VitalsSummaryResponse(BaseModel):
    user_id: int
    latest_steps_total: int
    latest_resting_hr: float | None
    latest_sleep_hours: float | None
    risk_flag: str
