from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import (
    ChallengeAssignment,
    ChallengeFrequency,
    DailyLog,
    ExerciseCategory,
    ExerciseEntry,
    FoodItem,
    InsulinScore,
    MealEntry,
    User,
    VitalsEntry,
)
from app.schemas.schemas import (
    AppleHealthImportRequest,
    ChallengeResponse,
    CoachingWaistResponse,
    CompleteChallengeRequest,
    CoachingMessageResponse,
    DailySummaryResponse,
    ExerciseSummaryResponse,
    LLMAnalyzeRequest,
    LLMAnalyzeResponse,
    LogExerciseRequest,
    LogFoodRequest,
    LogFoodResponse,
    LogVitalsRequest,
    NotificationEventRequest,
    NotificationSettingsResponse,
    ProfileResponse,
    UpdateNotificationSettingsRequest,
    UpdateProfileRequest,
    VitalsSummaryResponse,
    WhatsAppMessageRequest,
    WeeklySummaryResponse,
)
from app.services.apple_health_service import AppleHealthService
from app.services.challenge_engine import ChallengeEngine
from app.services.exercise_engine import is_supported_movement
from app.services.llm_service import llm_service
from app.services.notification_service import notification_service
from app.services.rule_engine import (
    calculate_daily_macros,
    evaluate_daily_status,
    get_or_create_metabolic_profile,
    validate_carb_limit,
    validate_fasting_window,
    validate_oil_limit,
    validate_protein_minimum,
)
from app.services.strength_engine import (
    compute_grip_improvement_percent,
    compute_monkey_bar_progress,
    compute_strength_score,
    compute_weekly_strength_graph,
    metabolic_strength_signals,
)
from app.services.vitals_engine import calculate_vitals_risk_score

router = APIRouter()


def _get_or_create_daily_log(db: Session, user_id: int, log_date):
    daily_log = db.scalar(select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date == log_date))
    if daily_log:
        return daily_log

    daily_log = DailyLog(user_id=user_id, log_date=log_date)
    db.add(daily_log)
    db.flush()
    return daily_log


@router.post("/log-food", response_model=LogFoodResponse)
def log_food(payload: LogFoodRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = get_or_create_metabolic_profile(db, user)

    if not validate_fasting_window(payload.consumed_at, profile.fasting_start_time, profile.fasting_end_time):
        raise HTTPException(status_code=400, detail="Meal is inside configured fasting window")

    food_ids = [entry.food_item_id for entry in payload.entries]
    foods = db.scalars(select(FoodItem).where(FoodItem.id.in_(food_ids))).all()
    food_map = {food.id: food for food in foods}
    if len(food_map) != len(set(food_ids)):
        raise HTTPException(status_code=404, detail="One or more food items not found")

    log_date = payload.consumed_at.date()
    daily_log = _get_or_create_daily_log(db, payload.user_id, log_date)

    for entry in payload.entries:
        db.add(
            MealEntry(
                daily_log_id=daily_log.id,
                food_item_id=entry.food_item_id,
                servings=entry.servings,
                consumed_at=payload.consumed_at,
            )
        )

    db.flush()

    meal_entries = db.scalars(
        select(MealEntry).options(joinedload(MealEntry.food_item)).where(MealEntry.daily_log_id == daily_log.id)
    ).all()

    macro_inputs = [
        {
            "protein": entry.food_item.protein,
            "carbs": entry.food_item.carbs,
            "fats": entry.food_item.fats,
            "hidden_oil_estimate": entry.food_item.hidden_oil_estimate,
            "servings": entry.servings,
        }
        for entry in meal_entries
    ]
    totals = calculate_daily_macros(macro_inputs)

    daily_log.total_protein = totals["protein"]
    daily_log.total_carbs = totals["carbs"]
    daily_log.total_fats = totals["fats"]
    daily_log.total_hidden_oil = totals["hidden_oil"]
    db.flush()

    daily_log = db.scalar(select(DailyLog).options(joinedload(DailyLog.user), joinedload(DailyLog.meal_entries)).where(DailyLog.id == daily_log.id))
    status = evaluate_daily_status(db, daily_log, profile)

    db.add(InsulinScore(daily_log_id=daily_log.id, score=status["insulin_load_score"], raw_score=status["insulin_load_raw_score"]))
    alerts = notification_service.evaluate_daily_alerts(db, payload.user_id, daily_log, status["insulin_load_score"])
    db.commit()

    validations = {
        "carb_limit": validate_carb_limit(totals["carbs"], profile.carb_ceiling),
        "oil_limit": validate_oil_limit(totals["hidden_oil"], profile.oil_limit_tsp),
        "protein_minimum": validate_protein_minimum(totals["protein"], profile.protein_target_min),
    }

    return LogFoodResponse(
        daily_log_id=daily_log.id,
        log_date=daily_log.log_date,
        total_protein=totals["protein"],
        total_carbs=totals["carbs"],
        total_fats=totals["fats"],
        total_hidden_oil=totals["hidden_oil"],
        insulin_load_score=status["insulin_load_score"],
        validations=validations,
    )


@router.get("/daily-summary", response_model=DailySummaryResponse)
def daily_summary(
    user_id: int = Query(default=1),
    date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    target_date = (date or datetime.utcnow()).date()
    daily_log = db.scalar(select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date == target_date))
    if not daily_log:
        raise HTTPException(status_code=404, detail="No daily log found")

    user = db.get(User, user_id)
    profile = get_or_create_metabolic_profile(db, user)
    latest_score = db.scalar(
        select(InsulinScore.score)
        .where(InsulinScore.daily_log_id == daily_log.id)
        .order_by(InsulinScore.calculated_at.desc())
        .limit(1)
    )

    validations = {
        "carb_limit": validate_carb_limit(daily_log.total_carbs, profile.carb_ceiling),
        "oil_limit": validate_oil_limit(daily_log.total_hidden_oil, profile.oil_limit_tsp),
        "protein_minimum": validate_protein_minimum(daily_log.total_protein, profile.protein_target_min),
    }

    return DailySummaryResponse(
        date=target_date,
        total_protein=daily_log.total_protein,
        total_carbs=daily_log.total_carbs,
        total_fats=daily_log.total_fats,
        total_hidden_oil=daily_log.total_hidden_oil,
        insulin_load_score=latest_score,
        validations=validations,
    )


@router.post("/log-vitals")
def log_vitals(payload: LogVitalsRequest, db: Session = Depends(get_db)):
    if not db.get(User, payload.user_id):
        raise HTTPException(status_code=404, detail="User not found")

    vitals = VitalsEntry(
        user_id=payload.user_id,
        recorded_at=payload.recorded_at or datetime.utcnow(),
        weight_kg=payload.weight_kg,
        fasting_glucose=payload.fasting_glucose,
        hba1c=payload.hba1c,
        triglycerides=payload.triglycerides,
        hdl=payload.hdl,
        resting_hr=payload.resting_hr,
        sleep_hours=payload.sleep_hours,
        waist_cm=payload.waist_cm,
        hrv=payload.hrv,
        vo2_max=payload.vo2_max,
        hr_zone_1_minutes=payload.hr_zone_1_minutes,
        hr_zone_2_minutes=payload.hr_zone_2_minutes,
        hr_zone_3_minutes=payload.hr_zone_3_minutes,
        hr_zone_4_minutes=payload.hr_zone_4_minutes,
        hr_zone_5_minutes=payload.hr_zone_5_minutes,
        steps_total=payload.steps_total,
        body_fat_percentage=payload.body_fat_percentage,
    )
    db.add(vitals)
    db.flush()

    prior_waist = db.scalar(
        select(VitalsEntry.waist_cm)
        .where(VitalsEntry.user_id == payload.user_id, VitalsEntry.id != vitals.id, VitalsEntry.waist_cm.is_not(None))
        .order_by(VitalsEntry.recorded_at.desc())
        .limit(1)
    )

    user = db.get(User, payload.user_id)
    profile = get_or_create_metabolic_profile(db, user)

    coaching_message = "Waist unchanged. Stay consistent with your current plan."
    waist_change_cm = 0.0
    carb_ceiling_adjusted = False

    if payload.waist_cm is not None and prior_waist is not None:
        waist_change_cm = round(payload.waist_cm - prior_waist, 2)
        if waist_change_cm < 0:
            coaching_message = f"Great work — waist dropped by {abs(waist_change_cm):.2f} cm. Keep the momentum!"
        elif waist_change_cm > 0:
            old_ceiling = profile.carb_ceiling
            profile.carb_ceiling = max(20, profile.carb_ceiling - 10)
            user.carb_ceiling = profile.carb_ceiling
            carb_ceiling_adjusted = profile.carb_ceiling != old_ceiling
            coaching_message = (
                f"Waist increased by {waist_change_cm:.2f} cm. Tightening carb ceiling to {profile.carb_ceiling}g for recovery."
            )

    db.commit()
    return {
        "status": "ok",
        "vitals_entry_id": vitals.id,
        "coaching": CoachingWaistResponse(
            message=coaching_message,
            waist_change_cm=waist_change_cm,
            carb_ceiling_adjusted=carb_ceiling_adjusted,
            carb_ceiling=profile.carb_ceiling,
        ).model_dump(),
    }


@router.post("/log-exercise")
def log_exercise(payload: LogExerciseRequest, db: Session = Depends(get_db)):
    if not db.get(User, payload.user_id):
        raise HTTPException(status_code=404, detail="User not found")

    if not is_supported_movement(payload.exercise_category, payload.movement_type):
        raise HTTPException(status_code=400, detail="Unsupported movement_type for category")

    daily_log = _get_or_create_daily_log(
        db,
        payload.user_id,
        (payload.performed_at or datetime.utcnow()).date(),
    )

    should_apply_walk_bonus = payload.exercise_category == ExerciseCategory.WALK and payload.duration_minutes >= 15

    entry = ExerciseEntry(
        user_id=payload.user_id,
        daily_log_id=daily_log.id,
        activity_type=payload.activity_type,
        exercise_category=payload.exercise_category,
        movement_type=payload.movement_type,
        muscle_group=payload.muscle_group,
        reps=payload.reps,
        sets=payload.sets,
        grip_intensity_score=payload.grip_intensity_score,
        pull_strength_score=payload.pull_strength_score,
        progression_level=payload.progression_level,
        dead_hang_duration_seconds=payload.dead_hang_duration_seconds,
        pull_up_count=payload.pull_up_count,
        assisted_pull_up_reps=payload.assisted_pull_up_reps,
        grip_endurance_seconds=payload.grip_endurance_seconds,
        duration_minutes=payload.duration_minutes,
        perceived_intensity=payload.perceived_intensity,
        step_count=payload.step_count,
        calories_estimate=payload.calories_estimate,
        calories_burned_estimate=payload.calories_burned_estimate,
        post_meal_walk=payload.post_meal_walk or should_apply_walk_bonus,
        performed_at=payload.performed_at or datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    return {"status": "ok", "exercise_entry_id": entry.id}


@router.get("/weekly-summary", response_model=WeeklySummaryResponse)
def weekly_summary(user_id: int = Query(default=1), db: Session = Depends(get_db)):
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=6)

    logs = db.scalars(
        select(DailyLog).where(
            DailyLog.user_id == user_id,
            DailyLog.log_date >= start_date,
            DailyLog.log_date <= end_date,
        )
    ).all()

    if not logs:
        return WeeklySummaryResponse(
            days_logged=0,
            avg_protein=0,
            avg_carbs=0,
            avg_fats=0,
            avg_hidden_oil=0,
            avg_insulin_load_score=0,
        )

    daily_ids = [log.id for log in logs]
    score_rows = db.scalars(select(InsulinScore.score).where(InsulinScore.daily_log_id.in_(daily_ids))).all()

    days = len(logs)
    return WeeklySummaryResponse(
        days_logged=days,
        avg_protein=round(sum(log.total_protein for log in logs) / days, 2),
        avg_carbs=round(sum(log.total_carbs for log in logs) / days, 2),
        avg_fats=round(sum(log.total_fats for log in logs) / days, 2),
        avg_hidden_oil=round(sum(log.total_hidden_oil for log in logs) / days, 2),
        avg_insulin_load_score=round(sum(score_rows) / len(score_rows), 2) if score_rows else 0,
    )


@router.get("/profile", response_model=ProfileResponse)
def get_profile(user_id: int = Query(default=1), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = get_or_create_metabolic_profile(db, user)
    db.commit()
    return ProfileResponse(
        user_id=user.id,
        protein_target_min=profile.protein_target_min,
        protein_target_max=profile.protein_target_max,
        carb_ceiling=profile.carb_ceiling,
        oil_limit_tsp=profile.oil_limit_tsp,
        fasting_start_time=profile.fasting_start_time,
        fasting_end_time=profile.fasting_end_time,
        max_chapati_per_day=profile.max_chapati_per_day,
        allow_rice=profile.allow_rice,
        chocolate_limit_per_day=profile.chocolate_limit_per_day,
        insulin_score_green_threshold=profile.insulin_score_green_threshold,
        insulin_score_yellow_threshold=profile.insulin_score_yellow_threshold,
    )


@router.put("/profile", response_model=ProfileResponse)
def put_profile(payload: UpdateProfileRequest, user_id: int = Query(default=1), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = get_or_create_metabolic_profile(db, user)

    updates = payload.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return ProfileResponse(
        user_id=user.id,
        protein_target_min=profile.protein_target_min,
        protein_target_max=profile.protein_target_max,
        carb_ceiling=profile.carb_ceiling,
        oil_limit_tsp=profile.oil_limit_tsp,
        fasting_start_time=profile.fasting_start_time,
        fasting_end_time=profile.fasting_end_time,
        max_chapati_per_day=profile.max_chapati_per_day,
        allow_rice=profile.allow_rice,
        chocolate_limit_per_day=profile.chocolate_limit_per_day,
        insulin_score_green_threshold=profile.insulin_score_green_threshold,
        insulin_score_yellow_threshold=profile.insulin_score_yellow_threshold,
    )


@router.get("/exercise-summary", response_model=ExerciseSummaryResponse)
def exercise_summary(user_id: int = Query(default=1), db: Session = Depends(get_db)):
    entries = db.scalars(select(ExerciseEntry).where(ExerciseEntry.user_id == user_id)).all()
    total_sessions = len(entries)
    total_duration = sum(entry.duration_minutes for entry in entries)
    total_steps = sum(entry.step_count or 0 for entry in entries)

    strength_score = compute_strength_score(entries)
    monkey_bar_progress = compute_monkey_bar_progress(entries)
    weekly_strength_graph = compute_weekly_strength_graph(entries)
    grip_strength_improvement_pct = compute_grip_improvement_percent(entries)
    metabolic_signals = metabolic_strength_signals(entries)

    return ExerciseSummaryResponse(
        user_id=user_id,
        total_sessions=total_sessions,
        total_duration_minutes=total_duration,
        total_steps=total_steps,
        strength_index=float(strength_score["strength_index"]),
        grip_strength_improvement_pct=grip_strength_improvement_pct,
        hdl_improvement_mode=bool(metabolic_signals["hdl_improvement_mode"]),
        muscle_stimulus_reduced=bool(metabolic_signals["muscle_stimulus_reduced"]),
        metabolic_message=str(metabolic_signals["metabolic_message"]),
        monkey_bar_progress=monkey_bar_progress,
        weekly_strength_graph=weekly_strength_graph,
    )


@router.get("/vitals-summary", response_model=VitalsSummaryResponse)
def vitals_summary(user_id: int = Query(default=1), db: Session = Depends(get_db)):
    vitals_entries = db.scalars(
        select(VitalsEntry).where(VitalsEntry.user_id == user_id).order_by(VitalsEntry.recorded_at.asc())
    ).all()
    if not vitals_entries:
        raise HTTPException(status_code=404, detail="No vitals data found")

    latest = vitals_entries[-1]
    risk = calculate_vitals_risk_score(vitals_entries)

    return VitalsSummaryResponse(
        user_id=user_id,
        latest_steps_total=latest.steps_total,
        latest_resting_hr=latest.resting_hr,
        latest_sleep_hours=latest.sleep_hours,
        risk_flag=risk["flag"],
    )


@router.post("/import-apple-health")
def import_apple_health(payload: AppleHealthImportRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    service = AppleHealthService(db)
    result = service.ingest(user, payload.model_dump())
    return {"status": "ok", **result}




def _challenge_payload(challenge: ChallengeAssignment, current_streak: int, longest_streak: int) -> ChallengeResponse:
    return ChallengeResponse(
        challenge_id=challenge.id,
        frequency=challenge.frequency.value,
        title=challenge.challenge_name,
        description=challenge.challenge_description,
        goal_metric=challenge.goal_metric,
        goal_target=challenge.goal_target,
        completed=challenge.completed,
        current_streak=current_streak,
        longest_streak=longest_streak,
        banner_title="7 Day Insulin Control Challenge",
    )


@router.get("/challenge", response_model=ChallengeResponse)
def get_daily_challenge(user_id: int = Query(default=1), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    engine = ChallengeEngine(db)
    challenge = engine.assign_for_today(user, ChallengeFrequency.DAILY)
    streak = engine.get_or_create_streak(user.id, ChallengeFrequency.DAILY)
    db.commit()
    return _challenge_payload(challenge, streak.current_streak, streak.longest_streak)


@router.get("/challenge/monthly", response_model=ChallengeResponse)
def get_monthly_challenge(user_id: int = Query(default=1), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    engine = ChallengeEngine(db)
    challenge = engine.assign_for_today(user, ChallengeFrequency.MONTHLY)
    streak = engine.get_or_create_streak(user.id, ChallengeFrequency.MONTHLY)
    db.commit()
    return _challenge_payload(challenge, streak.current_streak, streak.longest_streak)


@router.post("/challenge/complete", response_model=ChallengeResponse)
def complete_challenge(payload: CompleteChallengeRequest, db: Session = Depends(get_db)):
    challenge = db.scalar(
        select(ChallengeAssignment).where(
            ChallengeAssignment.id == payload.challenge_id,
            ChallengeAssignment.user_id == payload.user_id,
        )
    )
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    engine = ChallengeEngine(db)
    streak = engine.mark_completed(challenge)
    db.commit()
    return _challenge_payload(challenge, streak.current_streak, streak.longest_streak)

@router.post("/external-event")
def external_event(payload: dict):
    return {"status": "accepted", "message": "External event placeholder", "payload": payload}


@router.post("/whatsapp-message", response_model=CoachingMessageResponse)
def whatsapp_message(payload: WhatsAppMessageRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = get_or_create_metabolic_profile(db, user)
    consumed_at = payload.received_at or datetime.utcnow()
    analysis = llm_service.analyze(db, user, profile, payload.text, consumed_at)

    title = "Metabolic coaching response"
    body = (
        f"Status: {analysis['approval_status'].upper()}\n"
        f"Reason: {analysis['reasoning']}\n"
        f"Action: {analysis['recommended_adjustment']}"
    )
    notification_service.send_message(
        db,
        payload.user_id,
        channel="whatsapp",
        title=title,
        body=body,
        metadata={"food_items": analysis.get("food_items", [])},
    )
    db.commit()

    return CoachingMessageResponse(
        channel="whatsapp",
        title=title,
        body=body,
        insulin_load_delta=analysis["insulin_load_delta"],
        approval_status=analysis["approval_status"],
        suggested_action=analysis["recommended_adjustment"],
    )


@router.post("/notification-event")
def notification_event(payload: NotificationEventRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    title = f"Notification event: {payload.event_type}"
    body = f"Event payload accepted for processing ({payload.event_type})."
    result = notification_service.send_message(
        db,
        payload.user_id,
        channel="push",
        title=title,
        body=body,
        metadata=payload.payload,
    )
    db.commit()
    return {"status": "accepted", "delivery": result}


@router.get("/notification-settings", response_model=NotificationSettingsResponse)
def get_notification_settings(user_id: int = Query(default=1), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    settings = notification_service.get_or_create_settings(db, user_id)
    db.commit()
    return NotificationSettingsResponse(
        user_id=user_id,
        whatsapp_enabled=settings.whatsapp_enabled,
        push_enabled=settings.push_enabled,
        email_enabled=settings.email_enabled,
        silent_mode=settings.silent_mode,
    )


@router.put("/notification-settings", response_model=NotificationSettingsResponse)
def update_notification_settings(
    payload: UpdateNotificationSettingsRequest,
    user_id: int = Query(default=1),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    settings = notification_service.get_or_create_settings(db, user_id)
    updates = payload.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(settings, key, value)

    db.commit()
    db.refresh(settings)

    return NotificationSettingsResponse(
        user_id=user_id,
        whatsapp_enabled=settings.whatsapp_enabled,
        push_enabled=settings.push_enabled,
        email_enabled=settings.email_enabled,
        silent_mode=settings.silent_mode,
    )


@router.post("/llm/analyze", response_model=LLMAnalyzeResponse)
def llm_analyze(payload: LLMAnalyzeRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = get_or_create_metabolic_profile(db, user)
    consumed_at = payload.consumed_at or datetime.utcnow()
    analysis = llm_service.analyze(db, user, profile, payload.text, consumed_at)
    return LLMAnalyzeResponse(**analysis)
