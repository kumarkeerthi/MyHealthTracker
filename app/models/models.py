from datetime import date, datetime, timedelta
from enum import Enum

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    age: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sex: Mapped[str] = mapped_column(String(20), default="unspecified", nullable=False)
    triglycerides: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    hdl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    hba1c: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    insulin_resistant: Mapped[bool] = mapped_column(Boolean, default=True)
    diet_type: Mapped[str] = mapped_column(String(100), default="unspecified", nullable=False)
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
    challenge_assignments: Mapped[list["ChallengeAssignment"]] = relationship(back_populates="user")
    challenge_streaks: Mapped[list["ChallengeStreak"]] = relationship(back_populates="user")
    metabolic_recommendation_logs: Mapped[list["MetabolicRecommendationLog"]] = relationship(back_populates="user")
    habit_checkins: Mapped[list["HabitCheckin"]] = relationship(back_populates="user")
    metabolic_agent_state: Mapped["MetabolicAgentState"] = relationship(back_populates="user", uselist=False)
    pending_recommendations: Mapped[list["PendingRecommendation"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")
    auth_refresh_tokens: Mapped[list["AuthRefreshToken"]] = relationship(back_populates="user")
    auth_login_attempts: Mapped[list["AuthLoginAttempt"]] = relationship(back_populates="user")
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(back_populates="user")
    health_sync_summaries: Mapped[list["HealthSyncSummary"]] = relationship(back_populates="user")


class ExerciseCategory(str, Enum):
    WALK = "WALK"
    BODYWEIGHT = "BODYWEIGHT"
    MONKEY_BAR = "MONKEY_BAR"
    STRENGTH = "STRENGTH"


class ChallengeFrequency(str, Enum):
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"


class HabitChallengeType(str, Enum):
    STRICT = "STRICT"
    MICRO = "MICRO"
    SUPPORT = "SUPPORT"


class AgentRunCadence(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class RecommendationStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class MetabolicPhase(str, Enum):
    RESET = "RESET"
    STABILIZATION = "STABILIZATION"
    RECOMPOSITION = "RECOMPOSITION"
    PERFORMANCE = "PERFORMANCE"
    MAINTENANCE = "MAINTENANCE"


class AuthRefreshToken(Base):
    __tablename__ = "auth_refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    replaced_by_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)

    user: Mapped["User"] = relationship(back_populates="auth_refresh_tokens")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    hashed_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class AuthLoginAttempt(Base):
    __tablename__ = "auth_login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User | None"] = relationship(back_populates="auth_login_attempts")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="password_reset_tokens")




class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    route: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class LLMUsageDaily(Base):
    __tablename__ = "llm_usage_daily"
    __table_args__ = (UniqueConstraint("user_id", "usage_date", name="uq_llm_usage_daily_user_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    usage_date: Mapped[date] = mapped_column(Date, nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


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


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    silent_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    protein_reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    fasting_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    hydration_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    insulin_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    strength_reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    quiet_hours_start: Mapped[str | None] = mapped_column(String(5), nullable=True)
    quiet_hours_end: Mapped[str | None] = mapped_column(String(5), nullable=True)
    movement_reminder_delay_minutes: Mapped[int] = mapped_column(Integer, default=45)
    movement_sensitivity: Mapped[str] = mapped_column(String(20), default="balanced")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(600), nullable=False, unique=True)
    p256dh: Mapped[str] = mapped_column(String(255), nullable=False)
    auth: Mapped[str] = mapped_column(String(255), nullable=False)
    expiration_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FoodItem(Base):
    __tablename__ = "food_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    protein: Mapped[float] = mapped_column(Float, nullable=False)
    carbs: Mapped[float] = mapped_column(Float, nullable=False)
    fats: Mapped[float] = mapped_column(Float, nullable=False)
    sugar: Mapped[float] = mapped_column(Float, default=0.0)
    fiber: Mapped[float] = mapped_column(Float, default=0.0)
    glycemic_load: Mapped[float] = mapped_column(Float, nullable=False)
    hdl_support_score: Mapped[float] = mapped_column(Float, default=0.0)
    triglyceride_risk_weight: Mapped[float] = mapped_column(Float, default=0.0)
    food_group: Mapped[str] = mapped_column(String(30), default="general")
    high_carb_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    nut_seed_exception: Mapped[bool] = mapped_column(Boolean, default=False)
    hidden_oil_estimate: Mapped[float] = mapped_column(Float, nullable=False)

    meal_entries: Mapped[list["MealEntry"]] = relationship(back_populates="food_item")


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    ingredients: Mapped[str] = mapped_column(String(800), nullable=False)
    protein: Mapped[float] = mapped_column(Float, nullable=False)
    carbs: Mapped[float] = mapped_column(Float, nullable=False)
    fats: Mapped[float] = mapped_column(Float, nullable=False)
    cooking_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    oil_usage_tsp: Mapped[float] = mapped_column(Float, nullable=False)
    insulin_score_impact: Mapped[float] = mapped_column(Float, nullable=False)
    external_link_primary: Mapped[str | None] = mapped_column(String(300), nullable=True)
    external_link_secondary: Mapped[str | None] = mapped_column(String(300), nullable=True)


class DailyLog(Base):
    __tablename__ = "daily_logs"
    __table_args__ = (UniqueConstraint("user_id", "log_date", name="uq_user_log_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_protein: Mapped[float] = mapped_column(Float, default=0.0)
    total_carbs: Mapped[float] = mapped_column(Float, default=0.0)
    total_fats: Mapped[float] = mapped_column(Float, default=0.0)
    total_sugar: Mapped[float] = mapped_column(Float, default=0.0)
    total_fiber: Mapped[float] = mapped_column(Float, default=0.0)
    total_hdl_support: Mapped[float] = mapped_column(Float, default=0.0)
    total_triglyceride_risk: Mapped[float] = mapped_column(Float, default=0.0)
    total_hidden_oil: Mapped[float] = mapped_column(Float, default=0.0)
    water_ml: Mapped[int] = mapped_column(Integer, default=0)
    hydration_score: Mapped[float] = mapped_column(Float, default=0.0)
    dinner_meal: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    dinner_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dinner_logged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dinner_insulin_impact: Mapped[float] = mapped_column(Float, default=0.0)
    evening_insulin_spike_risk: Mapped[bool] = mapped_column(Boolean, default=False)

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
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    vision_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    manual_adjustment_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    portion_scale_factor: Mapped[float | None] = mapped_column(Float, nullable=True)

    daily_log: Mapped["DailyLog"] = relationship(back_populates="meal_entries")
    food_item: Mapped["FoodItem"] = relationship(back_populates="meal_entries")


class HealthSyncSummary(Base):
    __tablename__ = "health_sync_summaries"
    __table_args__ = (UniqueConstraint("user_id", "summary_date", name="uq_health_sync_user_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    summary_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    resting_hr: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    hrv: Mapped[float | None] = mapped_column(Float, nullable=True)
    workouts: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    source_generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="health_sync_summaries")




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


class MetabolicRecommendationLog(Base):
    __tablename__ = "metabolic_recommendation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    waist_not_dropping: Mapped[bool] = mapped_column(Boolean, default=False)
    strength_increasing: Mapped[bool] = mapped_column(Boolean, default=False)
    carb_ceiling_before: Mapped[int] = mapped_column(Integer, nullable=False)
    carb_ceiling_after: Mapped[int] = mapped_column(Integer, nullable=False)
    protein_target_min_before: Mapped[int] = mapped_column(Integer, nullable=False)
    protein_target_min_after: Mapped[int] = mapped_column(Integer, nullable=False)
    recommend_strength_volume_increase: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_refeed_meal: Mapped[bool] = mapped_column(Boolean, default=False)
    recommendations: Mapped[str] = mapped_column(Text, nullable=False)
    advisor_report: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="metabolic_recommendation_logs")


class MetabolicAgentState(Base):
    __tablename__ = "metabolic_agent_state"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    last_daily_scan: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_weekly_scan: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_monthly_review: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_carb_adjustment: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_protein_adjustment: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_strength_adjustment: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    carb_ceiling_current: Mapped[int] = mapped_column(Integer, default=90)
    protein_target_current: Mapped[int] = mapped_column(Integer, default=90)
    fruit_allowance_current: Mapped[int] = mapped_column(Integer, default=1)
    fruit_allowance_weekly: Mapped[int] = mapped_column(Integer, default=7)
    metabolic_phase: Mapped[MetabolicPhase] = mapped_column(
        SqlEnum(MetabolicPhase, name="metabolic_phase_enum"),
        default=MetabolicPhase.RESET,
    )
    metabolic_identity: Mapped[str] = mapped_column(String(40), default="Repair Mode")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="metabolic_agent_state")


class PendingRecommendation(Base):
    __tablename__ = "pending_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    cadence: Mapped[AgentRunCadence] = mapped_column(SqlEnum(AgentRunCadence, name="agent_run_cadence_enum"), nullable=False)
    recommendation_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence_level: Mapped[float] = mapped_column(Float, default=0.7)
    status: Mapped[RecommendationStatus] = mapped_column(
        SqlEnum(RecommendationStatus, name="pending_recommendation_status_enum"),
        default=RecommendationStatus.PENDING,
    )
    data_used: Mapped[str] = mapped_column(Text, nullable=False)
    threshold_triggered: Mapped[str] = mapped_column(String(220), nullable=False)
    historical_comparison: Mapped[str] = mapped_column(Text, nullable=False)
    llm_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="pending_recommendations")


class ChallengeAssignment(Base):
    __tablename__ = "challenge_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    frequency: Mapped[ChallengeFrequency] = mapped_column(
        SqlEnum(ChallengeFrequency, name="challenge_frequency_enum"),
        default=ChallengeFrequency.DAILY,
    )
    challenge_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    challenge_code: Mapped[str] = mapped_column(String(120), nullable=False)
    challenge_name: Mapped[str] = mapped_column(String(200), nullable=False)
    challenge_description: Mapped[str] = mapped_column(String(280), nullable=False)
    goal_metric: Mapped[str] = mapped_column(String(120), nullable=False)
    goal_target: Mapped[float] = mapped_column(Float, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="challenge_assignments")


class ChallengeStreak(Base):
    __tablename__ = "challenge_streaks"
    __table_args__ = (UniqueConstraint("user_id", "frequency", name="uq_user_challenge_frequency"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    frequency: Mapped[ChallengeFrequency] = mapped_column(
        SqlEnum(ChallengeFrequency, name="challenge_streak_frequency_enum"),
        default=ChallengeFrequency.DAILY,
    )
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_completed_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="challenge_streaks")


class HabitDefinition(Base):
    __tablename__ = "habit_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str] = mapped_column(String(280), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    challenge_type: Mapped[HabitChallengeType] = mapped_column(
        SqlEnum(HabitChallengeType, name="habit_challenge_type_enum"),
        default=HabitChallengeType.STRICT,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    checkins: Mapped[list["HabitCheckin"]] = relationship(back_populates="habit")


class HabitCheckin(Base):
    __tablename__ = "habit_checkins"
    __table_args__ = (UniqueConstraint("user_id", "habit_id", "habit_date", name="uq_user_habit_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habit_definitions.id"), nullable=False)
    habit_date: Mapped[date] = mapped_column(Date, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_reason: Mapped[str | None] = mapped_column(String(280), nullable=True)
    challenge_type_used: Mapped[HabitChallengeType] = mapped_column(
        SqlEnum(HabitChallengeType, name="habit_checkin_challenge_type_enum"),
        default=HabitChallengeType.STRICT,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="habit_checkins")
    habit: Mapped["HabitDefinition"] = relationship(back_populates="checkins")
