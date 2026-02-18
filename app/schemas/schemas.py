from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.models import ExerciseCategory
from app.models import MetabolicPhase


class MealEntryInput(BaseModel):
    food_item_id: int
    servings: float = Field(default=1.0, gt=0)


class LogFoodRequest(BaseModel):
    user_id: int = 1
    consumed_at: datetime
    entries: list[MealEntryInput]
    meal_context: str = "general"
    dinner_mode: str | None = None


class LogFoodResponse(BaseModel):
    daily_log_id: int
    log_date: date
    total_protein: float
    total_carbs: float
    total_fats: float
    total_sugar: float
    total_fiber: float
    total_hidden_oil: float
    insulin_load_score: float
    fruit_servings: float
    fruit_budget: float
    nuts_servings: float
    nuts_budget: float
    remaining_carb_budget: float
    suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    water_ml: int = 0
    hydration_score: float = 0
    hydration_target_min_ml: int = 2500
    hydration_target_max_ml: int = 3000
    hydration_target_achieved: bool = False
    validations: dict[str, bool]
    dinner_logged: bool = False
    dinner_carbs: float = 0
    dinner_protein: float = 0
    dinner_mode: str | None = None
    dinner_insulin_impact: float = 0
    evening_insulin_spike_risk: bool = False




class AnalyzedFoodItem(BaseModel):
    name: str
    estimated_quantity_grams: float
    confidence: float = Field(ge=0, le=1)
    estimated_protein: float
    estimated_carbs: float
    estimated_fat: float
    estimated_hidden_oil: float


class FoodImageValidationSummary(BaseModel):
    macro_totals_valid: bool
    food_ranges_valid: bool
    fasting_window_ok: bool
    carb_ceiling_ok: bool
    oil_limit_ok: bool
    chapati_limit_ok: bool
    low_confidence_flag: bool
    message: str


class FoodImageCoachingResponse(BaseModel):
    primary_message: str
    tags: list[str] = Field(default_factory=list)


class AnalyzeFoodImageResponse(BaseModel):
    foods: list[AnalyzedFoodItem]
    plate_estimated_total_calories: float
    overall_confidence: float = Field(ge=0, le=1)
    portion_scale_factor: float
    portion_estimation_confidence: str
    image_url: str
    estimated_macros: dict[str, float]
    estimated_oil_tsp: float
    insulin_load_impact: float
    projected_daily_insulin_score: float
    approval: str
    validation: FoodImageValidationSummary
    coaching: FoodImageCoachingResponse
    llm_prompt_template: str
    example_analysis_json: dict


class ConfirmFoodImageLogRequest(BaseModel):
    user_id: int = 1
    consumed_at: datetime | None = None
    meal_context: str | None = None
    foods: list[AnalyzedFoodItem]
    image_url: str
    vision_confidence: float = Field(ge=0, le=1)
    portion_scale_factor: float = 1.0
    manual_adjustment_flag: bool = False


class ConfirmFoodImageLogResponse(BaseModel):
    daily_log_id: int
    insulin_load_score: float
    total_protein: float
    total_carbs: float
    total_fats: float
    total_hidden_oil: float
    validations: dict[str, bool]
class LLMAnalyzeRequest(BaseModel):
    user_id: int = 1
    text: str = Field(min_length=1)
    consumed_at: datetime | None = None


class LLMAnalyzeResponse(BaseModel):
    approval_status: str
    reasoning: str
    insulin_load_delta: float
    recommended_adjustment: str
    food_items: list[str] = Field(default_factory=list)
    portion: str
    estimated_macros: dict[str, float]
    source: str


class RecipeResponse(BaseModel):
    id: int
    name: str
    ingredients: str
    macros: dict[str, float]
    cooking_time_minutes: int
    oil_usage_tsp: float
    insulin_score_impact: float
    external_links: list[str] = Field(default_factory=list)


class RecipeSuggestionResponse(BaseModel):
    user_id: int
    carb_load_remaining: float
    suggestion: str
    recipes: list[RecipeResponse]


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
    vo2_max: float | None = None
    hr_zone_1_minutes: int = 0
    hr_zone_2_minutes: int = 0
    hr_zone_3_minutes: int = 0
    hr_zone_4_minutes: int = 0
    hr_zone_5_minutes: int = 0
    steps_total: int = 0
    body_fat_percentage: float | None = None


class LogExerciseRequest(BaseModel):
    user_id: int = 1
    activity_type: str
    exercise_category: ExerciseCategory = ExerciseCategory.STRENGTH
    movement_type: str = "general"
    muscle_group: str = "full_body"
    reps: int | None = None
    sets: int | None = None
    grip_intensity_score: float = Field(default=0.0, ge=0)
    pull_strength_score: float = Field(default=0.0, ge=0)
    progression_level: int = Field(default=1, ge=1)
    dead_hang_duration_seconds: int | None = Field(default=None, ge=0)
    pull_up_count: int | None = Field(default=None, ge=0)
    assisted_pull_up_reps: int | None = Field(default=None, ge=0)
    grip_endurance_seconds: int | None = Field(default=None, ge=0)
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
    total_sugar: float = 0
    total_fiber: float = 0
    total_hidden_oil: float
    insulin_load_score: float | None
    fruit_servings: float = 0
    fruit_budget: float = 1
    nuts_servings: float = 0
    nuts_budget: float = 1
    remaining_carb_budget: float = 0
    warnings: list[str] = Field(default_factory=list)
    water_ml: int = 0
    hydration_score: float = 0
    hydration_target_min_ml: int = 2500
    hydration_target_max_ml: int = 3000
    hydration_target_achieved: bool = False
    validations: dict[str, bool]
    dinner_logged: bool = False
    dinner_carbs: float = 0
    dinner_protein: float = 0
    dinner_mode: str | None = None
    dinner_insulin_impact: float = 0
    evening_insulin_spike_risk: bool = False



class WeeklySummaryResponse(BaseModel):
    days_logged: int
    avg_protein: float
    avg_carbs: float
    avg_fats: float
    avg_hidden_oil: float
    avg_insulin_load_score: float


class MetabolicAdvisorReportResponse(BaseModel):
    user_id: int
    week_start: date
    week_end: date
    waist_not_dropping: bool
    strength_increasing: bool
    carb_ceiling_before: int
    carb_ceiling_after: int
    protein_target_min_before: int
    protein_target_min_after: int
    recommend_strength_volume_increase: bool
    allow_refeed_meal: bool
    recommendations: str
    advisor_report: str
    created_at: datetime


class AppleHealthImportRequest(BaseModel):
    user_id: int = 1
    health_export: dict | None = None
    relay: dict | None = None


class HealthWorkoutSyncPayload(BaseModel):
    type: str = Field(min_length=2, max_length=80)
    duration: int = Field(ge=1, le=1440)
    calories: float | None = Field(default=None, ge=0, le=10000)
    start_time: datetime


class HealthSummarySyncPayload(BaseModel):
    date: date
    steps: int = Field(ge=0, le=50000)
    resting_hr: float | None = Field(default=None, ge=25, le=220)
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    hrv: float | None = Field(default=None, ge=0, le=400)
    workouts: list[HealthWorkoutSyncPayload] = Field(default_factory=list, max_length=30)
    generated_at: datetime


class MonkeyBarProgressResponse(BaseModel):
    dead_hang_duration_seconds: int
    pull_up_count: int
    assisted_pull_up_reps: int
    grip_endurance_seconds: int


class StrengthScoreResponse(BaseModel):
    pushups: int
    pullups: int
    dead_hang_seconds: int
    squats: int
    strength_index: float


class ExerciseSummaryResponse(BaseModel):
    user_id: int
    total_sessions: int
    total_duration_minutes: int
    total_steps: int
    strength_index: float
    grip_strength_improvement_pct: float
    hdl_improvement_mode: bool
    muscle_stimulus_reduced: bool
    metabolic_message: str
    monkey_bar_progress: MonkeyBarProgressResponse
    weekly_strength_graph: list[float]




class AnalyticsPointResponse(BaseModel):
    date: date
    value: float


class TrendSeriesResponse(BaseModel):
    key: str
    label: str
    trend: str
    improving: bool
    points: list[AnalyticsPointResponse]


class MetabolicMomentumResponse(BaseModel):
    score: float
    insulin_load_component: float
    waist_component: float
    strength_component: float
    sleep_component: float


class AdvancedAnalyticsResponse(BaseModel):
    start_date: date
    end_date: date
    insulin_load_trend: TrendSeriesResponse
    fruit_frequency_trend: TrendSeriesResponse
    nut_frequency_trend: TrendSeriesResponse
    sugar_load_trend: TrendSeriesResponse
    hdl_support_trend: TrendSeriesResponse
    walk_vs_insulin_correlation: TrendSeriesResponse
    waist_trend: TrendSeriesResponse
    weight_trend: TrendSeriesResponse
    protein_intake_consistency: TrendSeriesResponse
    carb_intake_pattern: TrendSeriesResponse
    oil_usage_pattern: TrendSeriesResponse
    strength_score_trend: TrendSeriesResponse
    grip_strength_trend: TrendSeriesResponse
    sleep_trend: TrendSeriesResponse
    resting_heart_rate_trend: TrendSeriesResponse
    habit_compliance_trend: TrendSeriesResponse
    clean_streak_trend: TrendSeriesResponse
    metabolic_momentum: MetabolicMomentumResponse


class PhaseRuleResponse(BaseModel):
    carb_ceiling: str
    rice_rule: str
    fruit_rule: str
    strength_rule: str
    identity: str


class PhaseCatalogResponse(BaseModel):
    phase: MetabolicPhase
    identity: str
    carb_ceiling: str
    strength_rule: str


class PhaseModelResponse(BaseModel):
    current_phase: MetabolicPhase
    identity: str
    rules: PhaseRuleResponse
    all_phases: list[PhaseCatalogResponse]


class PhaseTransitionLogicResponse(BaseModel):
    should_transition: bool
    current_phase: MetabolicPhase
    target_phase: MetabolicPhase
    reason: str
    signals: dict[str, bool | float]


class CarbToleranceModuleResponse(BaseModel):
    carb_challenge_day_logged: bool
    protocol: str
    next_day_metrics: dict[str, float | None]
    carb_tolerance_index: float
    evaluation: str


class PerformanceDashboardResponse(BaseModel):
    strength_index: float
    grip_score: float
    carb_tolerance_index: float
    recovery_score: float
    sleep_consistency: float


class PeriodizationResponse(BaseModel):
    monthly_cycle: list[dict[str, str | int]]
    monkey_bar_metrics: dict[str, int]


class MetabolicPhasePerformanceResponse(BaseModel):
    phase_model: PhaseModelResponse
    transition_logic: PhaseTransitionLogicResponse
    carb_tolerance: CarbToleranceModuleResponse
    performance_dashboard: PerformanceDashboardResponse
    periodization: PeriodizationResponse
    example_transition_scenario: dict
    backend_logic: dict[str, str]


class VitalsSummaryResponse(BaseModel):
    user_id: int
    latest_steps_total: int
    latest_resting_hr: float | None
    latest_sleep_hours: float | None
    risk_flag: str


class WhatsAppMessageRequest(BaseModel):
    user_id: int = 1
    text: str = Field(min_length=1)
    received_at: datetime | None = None


class CoachingMessageResponse(BaseModel):
    channel: str
    title: str
    body: str
    insulin_load_delta: float
    approval_status: str
    suggested_action: str


class NotificationEventRequest(BaseModel):
    user_id: int = 1
    event_type: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)


class NotificationSettingsResponse(BaseModel):
    user_id: int
    whatsapp_enabled: bool
    push_enabled: bool
    email_enabled: bool
    silent_mode: bool
    protein_reminders_enabled: bool
    fasting_alerts_enabled: bool
    hydration_alerts_enabled: bool
    insulin_alerts_enabled: bool
    strength_reminders_enabled: bool
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    movement_reminder_delay_minutes: int = 45
    movement_sensitivity: str = "balanced"


class UpdateNotificationSettingsRequest(BaseModel):
    whatsapp_enabled: bool | None = None
    push_enabled: bool | None = None
    email_enabled: bool | None = None
    silent_mode: bool | None = None
    protein_reminders_enabled: bool | None = None
    fasting_alerts_enabled: bool | None = None
    hydration_alerts_enabled: bool | None = None
    insulin_alerts_enabled: bool | None = None
    strength_reminders_enabled: bool | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    movement_reminder_delay_minutes: int | None = None
    movement_sensitivity: str | None = None


class MovementPanelResponse(BaseModel):
    post_meal_walk_status: str
    steps_today: int
    walk_streak: int
    recovery_prompt: str
    badge: str | None = None
    alerts_remaining: int
    post_meal_walk_bonus: bool


class MovementSettingsResponse(BaseModel):
    user_id: int
    reminder_delay_minutes: int
    sensitivity: str
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None


class UpdateMovementSettingsRequest(BaseModel):
    reminder_delay_minutes: int | None = Field(default=None, ge=15, le=90)
    sensitivity: str | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None


class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscribeRequest(BaseModel):
    user_id: int = 1
    endpoint: str
    expirationTime: datetime | None = None
    keys: PushSubscriptionKeys
    user_agent: str | None = None


class PushSendRequest(BaseModel):
    user_id: int = 1
    title: str
    body: str
    payload: dict = Field(default_factory=dict)


class HydrationLogRequest(BaseModel):
    user_id: int = 1
    amount_ml: int = Field(gt=0, le=2000)
    log_date: date | None = None


class HydrationLogResponse(BaseModel):
    date: date
    water_ml: int
    hydration_score: float
    hydration_target_min_ml: int
    hydration_target_max_ml: int
    hydration_target_achieved: bool
    message: str


class ChallengeResponse(BaseModel):
    challenge_id: int
    frequency: str
    title: str
    description: str
    goal_metric: str
    goal_target: float
    completed: bool
    current_streak: int
    longest_streak: int
    banner_title: str


class CompleteChallengeRequest(BaseModel):
    challenge_id: int
    user_id: int = 1


class CoachingWaistResponse(BaseModel):
    message: str
    waist_change_cm: float
    carb_ceiling_adjusted: bool
    carb_ceiling: int


class HabitFailurePatternResponse(BaseModel):
    reason: str
    count: int


class HabitStatsResponse(BaseModel):
    habit_id: int
    code: str
    name: str
    description: str
    challenge_type: str
    recommended_challenge_type: str
    current_streak: int
    longest_streak: int
    success_rate: float
    failures: int
    failure_patterns: list[HabitFailurePatternResponse]


class HabitHeatmapCellResponse(BaseModel):
    date: date
    intensity: float
    count: int


class HabitIntelligenceResponse(BaseModel):
    habits: list[HabitStatsResponse]
    heatmap: list[HabitHeatmapCellResponse]
    insights: list[str]
    overall_success_rate: float


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


class AuthMeResponse(BaseModel):
    id: int
    email: str
    role: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)
