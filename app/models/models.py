from datetime import date, datetime
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[str] = mapped_column(String(20), nullable=False)
    triglycerides: Mapped[float] = mapped_column(Float, nullable=False)
    hdl: Mapped[float] = mapped_column(Float, nullable=False)
    hba1c: Mapped[float] = mapped_column(Float, nullable=False)
    insulin_resistant: Mapped[bool] = mapped_column(Boolean, default=True)
    diet_type: Mapped[str] = mapped_column(String(100), nullable=False)
    eating_window_start: Mapped[str] = mapped_column(String(5), default="08:00")
    eating_window_end: Mapped[str] = mapped_column(String(5), default="14:00")
    max_chapati_per_day: Mapped[int] = mapped_column(Integer, default=2)
    no_rice_reset: Mapped[bool] = mapped_column(Boolean, default=True)
    eggs_per_day: Mapped[int] = mapped_column(Integer, default=3)
    whey_per_day: Mapped[int] = mapped_column(Integer, default=1)
    dark_chocolate_max_squares: Mapped[int] = mapped_column(Integer, default=2)
    oil_limit_tsp: Mapped[float] = mapped_column(Float, default=3.0)
    protein_target_min: Mapped[int] = mapped_column(Integer, default=90)
    protein_target_max: Mapped[int] = mapped_column(Integer, default=110)
    carb_ceiling: Mapped[int] = mapped_column(Integer, default=90)

    daily_logs: Mapped[list["DailyLog"]] = relationship(back_populates="user")
    vitals_entries: Mapped[list["VitalsEntry"]] = relationship(back_populates="user")
    exercise_entries: Mapped[list["ExerciseEntry"]] = relationship(back_populates="user")
    metabolic_profile: Mapped["MetabolicProfile"] = relationship(back_populates="user", uselist=False)


class ExerciseCategory(str, Enum):
    WALK = "WALK"
    BODYWEIGHT = "BODYWEIGHT"
    MONKEY_BAR = "MONKEY_BAR"
    STRENGTH = "STRENGTH"


class MetabolicProfile(Base):
    __tablename__ = "metabolic_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    protein_target_min: Mapped[int] = mapped_column(Integer, default=90)
    protein_target_max: Mapped[int] = mapped_column(Integer, default=110)
    carb_ceiling: Mapped[int] = mapped_column(Integer, default=90)
    oil_limit_tsp: Mapped[float] = mapped_column(Float, default=3.0)
    fasting_start_time: Mapped[str] = mapped_column(String(5), default="14:00")
    fasting_end_time: Mapped[str] = mapped_column(String(5), default="08:00")
    max_chapati_per_day: Mapped[int] = mapped_column(Integer, default=2)
    allow_rice: Mapped[bool] = mapped_column(Boolean, default=False)
    chocolate_limit_per_day: Mapped[int] = mapped_column(Integer, default=2)
    insulin_score_green_threshold: Mapped[float] = mapped_column(Float, default=40)
    insulin_score_yellow_threshold: Mapped[float] = mapped_column(Float, default=70)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="metabolic_profile")


class FoodItem(Base):
    __tablename__ = "food_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    protein: Mapped[float] = mapped_column(Float, nullable=False)
    carbs: Mapped[float] = mapped_column(Float, nullable=False)
    fats: Mapped[float] = mapped_column(Float, nullable=False)
    glycemic_load: Mapped[float] = mapped_column(Float, nullable=False)
    hidden_oil_estimate: Mapped[float] = mapped_column(Float, nullable=False)

    meal_entries: Mapped[list["MealEntry"]] = relationship(back_populates="food_item")


class DailyLog(Base):
    __tablename__ = "daily_logs"
    __table_args__ = (UniqueConstraint("user_id", "log_date", name="uq_user_log_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_protein: Mapped[float] = mapped_column(Float, default=0.0)
    total_carbs: Mapped[float] = mapped_column(Float, default=0.0)
    total_fats: Mapped[float] = mapped_column(Float, default=0.0)
    total_hidden_oil: Mapped[float] = mapped_column(Float, default=0.0)

    user: Mapped["User"] = relationship(back_populates="daily_logs")
    meal_entries: Mapped[list["MealEntry"]] = relationship(back_populates="daily_log")
    insulin_scores: Mapped[list["InsulinScore"]] = relationship(back_populates="daily_log")


class MealEntry(Base):
    __tablename__ = "meal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    daily_log_id: Mapped[int] = mapped_column(ForeignKey("daily_logs.id"), nullable=False)
    food_item_id: Mapped[int] = mapped_column(ForeignKey("food_items.id"), nullable=False)
    consumed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    servings: Mapped[float] = mapped_column(Float, default=1.0)

    daily_log: Mapped["DailyLog"] = relationship(back_populates="meal_entries")
    food_item: Mapped["FoodItem"] = relationship(back_populates="meal_entries")


class VitalsEntry(Base):
    __tablename__ = "vitals_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    weight_kg: Mapped[float] = mapped_column(Float)
    fasting_glucose: Mapped[float] = mapped_column(Float)
    hba1c: Mapped[float] = mapped_column(Float)
    triglycerides: Mapped[float] = mapped_column(Float)
    hdl: Mapped[float] = mapped_column(Float)
    resting_hr: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    hrv: Mapped[float | None] = mapped_column(Float, nullable=True)
    vo2_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    hr_zone_1_minutes: Mapped[int] = mapped_column(Integer, default=0)
    hr_zone_2_minutes: Mapped[int] = mapped_column(Integer, default=0)
    hr_zone_3_minutes: Mapped[int] = mapped_column(Integer, default=0)
    hr_zone_4_minutes: Mapped[int] = mapped_column(Integer, default=0)
    hr_zone_5_minutes: Mapped[int] = mapped_column(Integer, default=0)
    steps_total: Mapped[int] = mapped_column(Integer, default=0)
    body_fat_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)

    user: Mapped["User"] = relationship(back_populates="vitals_entries")


class ExerciseEntry(Base):
    __tablename__ = "exercise_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    daily_log_id: Mapped[int | None] = mapped_column(ForeignKey("daily_logs.id"), nullable=True)
    activity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    exercise_category: Mapped[ExerciseCategory] = mapped_column(
        SqlEnum(ExerciseCategory, name="exercise_category_enum"),
        default=ExerciseCategory.STRENGTH,
    )
    movement_type: Mapped[str] = mapped_column(String(120), default="general")
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    muscle_group: Mapped[str] = mapped_column(String(100), default="full_body")
    grip_intensity_score: Mapped[float] = mapped_column(Float, default=0.0)
    pull_strength_score: Mapped[float] = mapped_column(Float, default=0.0)
    progression_level: Mapped[int] = mapped_column(Integer, default=1)
    dead_hang_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pull_up_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assisted_pull_up_reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grip_endurance_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    calories_burned_estimate: Mapped[float] = mapped_column(Float, default=0.0)
    perceived_intensity: Mapped[int] = mapped_column(Integer, default=5)
    step_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calories_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    post_meal_walk: Mapped[bool] = mapped_column(Boolean, default=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="exercise_entries")


class InsulinScore(Base):
    __tablename__ = "insulin_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    daily_log_id: Mapped[int] = mapped_column(ForeignKey("daily_logs.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    raw_score: Mapped[float] = mapped_column(Float, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    daily_log: Mapped["DailyLog"] = relationship(back_populates="insulin_scores")
