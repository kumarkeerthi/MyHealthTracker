from datetime import date, datetime

from pydantic import BaseModel, Field


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


class LogExerciseRequest(BaseModel):
    user_id: int = 1
    activity_type: str
    duration_minutes: int = Field(gt=0)
    calories_burned_estimate: float = 0.0
    post_meal_walk: bool = False
    performed_at: datetime | None = None


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
