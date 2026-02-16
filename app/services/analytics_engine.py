from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyLog, ExerciseEntry, FoodItem, InsulinScore, MealEntry, User, VitalsEntry
from app.services.strength_engine import compute_strength_score


class AnalyticsEngine:
    def _normalize(self, value: float, floor: float, ceiling: float) -> float:
        if ceiling <= floor:
            return 0.0
        bounded = min(max(value, floor), ceiling)
        return (bounded - floor) / (ceiling - floor)

    def _trend_meta(self, start: float, end: float, lower_is_better: bool) -> tuple[str, bool]:
        delta = end - start
        improving = delta < 0 if lower_is_better else delta > 0
        if abs(delta) < 0.05:
            return "steady", False
        if improving:
            return "improvement", True
        return "regression", False

    def _build_series(self, label: str, values: list[tuple[date, float]], lower_is_better: bool):
        points = [{"date": row_date, "value": round(value, 2)} for row_date, value in values]
        start = points[0]["value"] if points else 0.0
        end = points[-1]["value"] if points else 0.0
        trend, improving = self._trend_meta(start, end, lower_is_better)
        return {
            "key": label.lower().replace(" ", "_"),
            "label": label,
            "trend": trend,
            "improving": improving,
            "points": points,
        }

    def build_advanced_analytics(self, db: Session, user_id: int, days: int = 30):
        end_date = date.today()
        start_date = end_date - timedelta(days=max(6, days - 1))

        user = db.get(User, user_id)
        if not user:
            return None

        daily_logs = db.scalars(
            select(DailyLog)
            .where(DailyLog.user_id == user_id, DailyLog.log_date >= start_date, DailyLog.log_date <= end_date)
            .order_by(DailyLog.log_date.asc())
        ).all()
        vitals = db.scalars(
            select(VitalsEntry)
            .where(VitalsEntry.user_id == user_id, VitalsEntry.recorded_at >= start_date, VitalsEntry.recorded_at <= end_date + timedelta(days=1))
            .order_by(VitalsEntry.recorded_at.asc())
        ).all()
        exercise_entries = db.scalars(
            select(ExerciseEntry)
            .where(ExerciseEntry.user_id == user_id, ExerciseEntry.performed_at >= start_date, ExerciseEntry.performed_at <= end_date + timedelta(days=1))
            .order_by(ExerciseEntry.performed_at.asc())
        ).all()

        score_rows = db.execute(
            select(DailyLog.log_date, InsulinScore.score)
            .join(InsulinScore, InsulinScore.daily_log_id == DailyLog.id)
            .where(DailyLog.user_id == user_id, DailyLog.log_date >= start_date, DailyLog.log_date <= end_date)
            .order_by(DailyLog.log_date.asc(), InsulinScore.calculated_at.asc())
        ).all()

        insulin_by_date: dict[date, float] = {}
        for log_date, score in score_rows:
            insulin_by_date[log_date] = float(score)

        vitals_by_day: dict[date, VitalsEntry] = {}
        for row in vitals:
            vitals_by_day[row.recorded_at.date()] = row

        exercise_by_day: dict[date, list[ExerciseEntry]] = {}
        for row in exercise_entries:
            exercise_by_day.setdefault(row.performed_at.date(), []).append(row)

        clean_streak = 0
        clean_streak_points: list[tuple[date, float]] = []
        compliance_points: list[tuple[date, float]] = []
        protein_points: list[tuple[date, float]] = []
        carb_points: list[tuple[date, float]] = []
        oil_points: list[tuple[date, float]] = []
        insulin_points: list[tuple[date, float]] = []
        weight_points: list[tuple[date, float]] = []
        waist_points: list[tuple[date, float]] = []
        sleep_points: list[tuple[date, float]] = []
        hr_points: list[tuple[date, float]] = []
        strength_points: list[tuple[date, float]] = []
        grip_points: list[tuple[date, float]] = []
        fruit_points: list[tuple[date, float]] = []
        nut_points: list[tuple[date, float]] = []
        sugar_points: list[tuple[date, float]] = []
        hdl_support_points: list[tuple[date, float]] = []

        cursor = start_date
        while cursor <= end_date:
            log = next((d for d in daily_logs if d.log_date == cursor), None)
            vitals_entry = vitals_by_day.get(cursor)
            day_exercises = exercise_by_day.get(cursor, [])

            protein = float(log.total_protein) if log else 0.0
            carbs = float(log.total_carbs) if log else 0.0
            oil = float(log.total_hidden_oil) if log else 0.0
            sugar = float(getattr(log, "total_sugar", 0.0) or 0.0) if log else 0.0
            hdl_support = float(getattr(log, "total_hdl_support", 0.0) or 0.0) if log else 0.0
            insulin = insulin_by_date.get(cursor, max(0.0, carbs + oil * 4 - protein * 0.25))

            protein_ok = protein >= user.protein_target_min
            carb_ok = carbs <= user.carb_ceiling
            oil_ok = oil <= user.oil_limit_tsp
            compliance = ((1 if protein_ok else 0) + (1 if carb_ok else 0) + (1 if oil_ok else 0)) / 3 * 100

            if protein_ok and carb_ok and oil_ok:
                clean_streak += 1
            else:
                clean_streak = 0

            strength_score = compute_strength_score(day_exercises) if day_exercises else 0.0
            avg_grip = 0.0
            if day_exercises:
                grip_values = [entry.grip_intensity_score for entry in day_exercises if entry.grip_intensity_score is not None]
                if grip_values:
                    avg_grip = sum(grip_values) / len(grip_values)

            protein_points.append((cursor, protein))
            carb_points.append((cursor, carbs))
            oil_points.append((cursor, oil))
            sugar_points.append((cursor, sugar))
            hdl_support_points.append((cursor, hdl_support))
            insulin_points.append((cursor, insulin))
            compliance_points.append((cursor, compliance))
            clean_streak_points.append((cursor, float(clean_streak)))
            strength_points.append((cursor, float(strength_score)))
            grip_points.append((cursor, float(avg_grip)))

            fruit_servings = 0.0
            nut_servings = 0.0
            if log:
                day_entries = db.scalars(
                    select(MealEntry)
                    .join(FoodItem, FoodItem.id == MealEntry.food_item_id)
                    .where(MealEntry.daily_log_id == log.id)
                ).all()
                fruit_servings = sum(entry.servings for entry in day_entries if entry.food_item.food_group == "fruit")
                nut_servings = sum(
                    entry.servings for entry in day_entries if entry.food_item.food_group == "nut" and not entry.food_item.nut_seed_exception
                )
            fruit_points.append((cursor, float(fruit_servings)))
            nut_points.append((cursor, float(nut_servings)))

            if vitals_entry and vitals_entry.weight_kg is not None:
                weight_points.append((cursor, float(vitals_entry.weight_kg)))
            if vitals_entry and vitals_entry.waist_cm is not None:
                waist_points.append((cursor, float(vitals_entry.waist_cm)))
            if vitals_entry and vitals_entry.sleep_hours is not None:
                sleep_points.append((cursor, float(vitals_entry.sleep_hours)))
            if vitals_entry and vitals_entry.resting_hr is not None:
                hr_points.append((cursor, float(vitals_entry.resting_hr)))

            cursor += timedelta(days=1)

        def with_fallback(points: list[tuple[date, float]]):
            return points if points else [(start_date, 0.0), (end_date, 0.0)]

        insulin_points = with_fallback(insulin_points)
        waist_points = with_fallback(waist_points)
        strength_points = with_fallback(strength_points)
        sleep_points = with_fallback(sleep_points)

        insulin_component = (1 - self._normalize(insulin_points[-1][1], 10, 90)) * 100
        waist_baseline = waist_points[0][1]
        waist_delta = waist_baseline - waist_points[-1][1]
        waist_component = self._normalize(waist_delta, -5, 8) * 100
        strength_delta = strength_points[-1][1] - strength_points[0][1]
        strength_component = self._normalize(strength_delta, -10, 20) * 100
        sleep_component = self._normalize(sleep_points[-1][1], 4, 8.5) * 100
        momentum = (insulin_component * 0.3) + (waist_component * 0.3) + (strength_component * 0.25) + (sleep_component * 0.15)

        return {
            "start_date": start_date,
            "end_date": end_date,
            "insulin_load_trend": self._build_series("Insulin Load Trend", insulin_points, lower_is_better=True),
            "fruit_frequency_trend": self._build_series("Fruit Frequency", fruit_points, lower_is_better=True),
            "nut_frequency_trend": self._build_series("Nut Frequency", nut_points, lower_is_better=False),
            "sugar_load_trend": self._build_series("Sugar Load Trend", sugar_points, lower_is_better=True),
            "hdl_support_trend": self._build_series("HDL-support Trend", hdl_support_points, lower_is_better=False),
            "waist_trend": self._build_series("Waist Trend", with_fallback(waist_points), lower_is_better=True),
            "weight_trend": self._build_series("Weight Trend", with_fallback(weight_points), lower_is_better=True),
            "protein_intake_consistency": self._build_series("Protein Intake Consistency", protein_points, lower_is_better=False),
            "carb_intake_pattern": self._build_series("Carb Intake Pattern", carb_points, lower_is_better=True),
            "oil_usage_pattern": self._build_series("Oil Usage Pattern", oil_points, lower_is_better=True),
            "strength_score_trend": self._build_series("Strength Score Trend", strength_points, lower_is_better=False),
            "grip_strength_trend": self._build_series("Grip Strength (Monkey Bar) Trend", grip_points, lower_is_better=False),
            "sleep_trend": self._build_series("Sleep Trend", with_fallback(sleep_points), lower_is_better=False),
            "resting_heart_rate_trend": self._build_series("Resting Heart Rate Trend", with_fallback(hr_points), lower_is_better=True),
            "habit_compliance_trend": self._build_series("Habit Compliance Trend", compliance_points, lower_is_better=False),
            "clean_streak_trend": self._build_series("Clean Streak Graph", clean_streak_points, lower_is_better=False),
            "metabolic_momentum": {
                "score": round(momentum, 2),
                "insulin_load_component": round(insulin_component, 2),
                "waist_component": round(waist_component, 2),
                "strength_component": round(strength_component, 2),
                "sleep_component": round(sleep_component, 2),
            },
        }


analytics_engine = AnalyticsEngine()
