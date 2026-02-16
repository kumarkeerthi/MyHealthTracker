from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import DailyLog, ExerciseEntry, FoodItem, InsulinScore, MealEntry, User, VitalsEntry
from app.schemas.schemas import (
    DailySummaryResponse,
    LogExerciseRequest,
    LogFoodRequest,
    LogFoodResponse,
    LogVitalsRequest,
    WeeklySummaryResponse,
)
from app.services.rule_engine import (
    calculate_daily_macros,
    calculate_insulin_load_score,
    validate_carb_limit,
    validate_fasting_window,
    validate_oil_limit,
    validate_protein_minimum,
)

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

    if not validate_fasting_window(payload.consumed_at, user.eating_window_start, user.eating_window_end):
        raise HTTPException(status_code=400, detail="Meal is outside configured eating window")

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

    post_meal_walk_count = db.scalar(
        select(func.count(ExerciseEntry.id)).where(
            ExerciseEntry.daily_log_id == daily_log.id, ExerciseEntry.post_meal_walk.is_(True)
        )
    )
    score, raw_score = calculate_insulin_load_score(
        totals["carbs"], totals["hidden_oil"], totals["protein"], float(post_meal_walk_count or 0)
    )

    daily_log.total_protein = totals["protein"]
    daily_log.total_carbs = totals["carbs"]
    daily_log.total_fats = totals["fats"]
    daily_log.total_hidden_oil = totals["hidden_oil"]

    db.add(InsulinScore(daily_log_id=daily_log.id, score=score, raw_score=raw_score))
    db.commit()

    validations = {
        "carb_limit": validate_carb_limit(totals["carbs"], user.carb_ceiling),
        "oil_limit": validate_oil_limit(totals["hidden_oil"], user.oil_limit_tsp),
        "protein_minimum": validate_protein_minimum(totals["protein"], user.protein_target_min),
    }

    return LogFoodResponse(
        daily_log_id=daily_log.id,
        log_date=daily_log.log_date,
        total_protein=totals["protein"],
        total_carbs=totals["carbs"],
        total_fats=totals["fats"],
        total_hidden_oil=totals["hidden_oil"],
        insulin_load_score=score,
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
    latest_score = db.scalar(
        select(InsulinScore.score)
        .where(InsulinScore.daily_log_id == daily_log.id)
        .order_by(InsulinScore.calculated_at.desc())
        .limit(1)
    )

    validations = {
        "carb_limit": validate_carb_limit(daily_log.total_carbs, user.carb_ceiling),
        "oil_limit": validate_oil_limit(daily_log.total_hidden_oil, user.oil_limit_tsp),
        "protein_minimum": validate_protein_minimum(daily_log.total_protein, user.protein_target_min),
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
    )
    db.add(vitals)
    db.commit()
    return {"status": "ok", "vitals_entry_id": vitals.id}


@router.post("/log-exercise")
def log_exercise(payload: LogExerciseRequest, db: Session = Depends(get_db)):
    if not db.get(User, payload.user_id):
        raise HTTPException(status_code=404, detail="User not found")

    daily_log = _get_or_create_daily_log(
        db,
        payload.user_id,
        (payload.performed_at or datetime.utcnow()).date(),
    )

    entry = ExerciseEntry(
        user_id=payload.user_id,
        daily_log_id=daily_log.id,
        activity_type=payload.activity_type,
        duration_minutes=payload.duration_minutes,
        calories_burned_estimate=payload.calories_burned_estimate,
        post_meal_walk=payload.post_meal_walk,
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
    score_rows = db.scalars(
        select(InsulinScore.score).where(InsulinScore.daily_log_id.in_(daily_ids))
    ).all()

    days = len(logs)
    return WeeklySummaryResponse(
        days_logged=days,
        avg_protein=round(sum(log.total_protein for log in logs) / days, 2),
        avg_carbs=round(sum(log.total_carbs for log in logs) / days, 2),
        avg_fats=round(sum(log.total_fats for log in logs) / days, 2),
        avg_hidden_oil=round(sum(log.total_hidden_oil for log in logs) / days, 2),
        avg_insulin_load_score=round(sum(score_rows) / len(score_rows), 2) if score_rows else 0,
    )
