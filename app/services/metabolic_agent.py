import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AgentRunCadence,
    DailyLog,
    ExerciseCategory,
    ExerciseEntry,
    HabitCheckin,
    HabitDefinition,
    InsulinScore,
    FoodItem,
    MealEntry,
    MetabolicAgentState,
    MetabolicProfile,
    PendingRecommendation,
    User,
    VitalsEntry,
)
from app.services.llm_service import llm_service
from app.services.strength_engine import compute_strength_score


@dataclass
class AgentRecommendation:
    recommendation_type: str
    title: str
    summary: str
    confidence_level: float
    data_used: dict
    threshold_triggered: str
    historical_comparison: str


class MetabolicAgentService:
    def run_daily_scan_for_all_users(self, db: Session) -> int:
        users = db.scalars(select(User.id)).all()
        count = 0
        for user_id in users:
            if self.run_daily_scan(db, user_id):
                count += 1
        db.commit()
        return count

    def run_weekly_analysis_for_all_users(self, db: Session) -> int:
        users = db.scalars(select(User.id)).all()
        count = 0
        for user_id in users:
            if self.run_weekly_analysis(db, user_id):
                count += 1
        db.commit()
        return count

    def run_monthly_review_for_all_users(self, db: Session) -> int:
        users = db.scalars(select(User.id)).all()
        count = 0
        for user_id in users:
            if self.run_monthly_review(db, user_id):
                count += 1
        db.commit()
        return count

    def run_daily_scan(self, db: Session, user_id: int) -> bool:
        user = db.get(User, user_id)
        if not user:
            return False

        state = self._get_or_create_agent_state(db, user)
        profile = self._get_or_create_profile(db, user)
        end_day = datetime.utcnow().date()
        start_day = end_day - timedelta(days=2)

        insulin_by_day = self._daily_insulin_map(db, user_id, start_day, end_day)
        carb_logs = db.scalars(
            select(DailyLog).where(
                DailyLog.user_id == user_id,
                DailyLog.log_date >= start_day,
                DailyLog.log_date <= end_day,
            )
        ).all()

        daily_recommendations: list[AgentRecommendation] = []

        high_insulin_days = [datetime.strptime(d, "%Y-%m-%d").date() for d, score in insulin_by_day if score > 70]
        if self._has_consecutive_days(high_insulin_days):
            daily_recommendations.append(
                AgentRecommendation(
                    recommendation_type="daily_carb_reduction",
                    title="Reduce carb intake tomorrow",
                    summary="Insulin load was above 70 on at least two recent days. Reduce carb intake tomorrow.",
                    confidence_level=0.84,
                    data_used={"insulin_load_last_3_days": insulin_by_day},
                    threshold_triggered="Insulin load > 70 for two consecutive days.",
                    historical_comparison=f"High-insulin days in last 3-day window: {len(high_insulin_days)} (consecutive rule satisfied).",
                )
            )

        low_protein_days = [str(log.log_date) for log in carb_logs if float(log.total_protein or 0) < 80]
        if len(low_protein_days) >= 2:
            daily_recommendations.append(
                AgentRecommendation(
                    recommendation_type="daily_protein_support",
                    title="Add whey tomorrow",
                    summary="Protein intake was below 80g on two recent days. Add whey tomorrow.",
                    confidence_level=0.87,
                    data_used={"protein_last_3_days": [{"day": str(log.log_date), "protein_g": float(log.total_protein or 0)} for log in carb_logs]},
                    threshold_triggered="Protein intake < 80g for two days.",
                    historical_comparison=f"Days below 80g protein in last 3-day window: {len(low_protein_days)}.",
                )
            )

        fasting_violations = self._count_fasting_violations(db, user_id, start_day, end_day, profile)
        hydration_compliance = self._hydration_compliance(db, user_id, start_day, end_day)
        strength_logged = self._strength_sessions(db, user_id, start_day, end_day)

        state.last_daily_scan = datetime.utcnow()
        state.notes = (
            f"Daily scan {end_day}: fasting_violations={fasting_violations}, "
            f"hydration_compliance={hydration_compliance}, strength_sessions={strength_logged}"
        )

        for rec in daily_recommendations:
            self._create_pending_recommendation(db, user_id, AgentRunCadence.DAILY, rec)

        return True

    def run_weekly_analysis(self, db: Session, user_id: int) -> bool:
        user = db.get(User, user_id)
        if not user:
            return False

        state = self._get_or_create_agent_state(db, user)
        profile = self._get_or_create_profile(db, user)
        end_day = datetime.utcnow().date()
        start_day = end_day - timedelta(days=6)
        previous_start = start_day - timedelta(days=7)
        previous_end = start_day - timedelta(days=1)

        waist_recent = self._average_waist(db, user_id, start_day, end_day)
        waist_previous = self._average_waist(db, user_id, previous_start, previous_end)
        waist_not_reducing = waist_recent is not None and waist_previous is not None and waist_recent >= waist_previous

        strength_recent = self._strength_index(db, user_id, start_day, end_day)
        strength_previous = self._strength_index(db, user_id, previous_start, previous_end)
        strength_rising = strength_recent > strength_previous

        rhr_recent = self._avg_vitals_metric(db, user_id, start_day, end_day, VitalsEntry.resting_hr)
        sleep_recent = self._avg_vitals_metric(db, user_id, start_day, end_day, VitalsEntry.sleep_hours)
        fruit_frequency = self._fruit_frequency(db, user_id, start_day, end_day)
        oil_average = self._avg_daily_oil(db, user_id, start_day, end_day)
        restaurant_frequency = self._restaurant_image_frequency(db, user_id, start_day, end_day)
        hdl_support_days = self._hdl_support_days(db, user_id, start_day, end_day)
        hdl_recent = self._avg_vitals_metric(db, user_id, start_day, end_day, VitalsEntry.hdl)
        hdl_previous = self._avg_vitals_metric(db, user_id, previous_start, previous_end, VitalsEntry.hdl)
        hdl_improving = hdl_recent is not None and hdl_previous is not None and hdl_recent > hdl_previous

        weekly_recommendations: list[AgentRecommendation] = []

        if waist_not_reducing and profile.carb_ceiling > 80:
            proposed_carb = profile.carb_ceiling - 10
            weekly_recommendations.append(
                AgentRecommendation(
                    recommendation_type="weekly_carb_ceiling_adjustment",
                    title="Reduce carb ceiling by 10g",
                    summary=f"Waist is not reducing and carb ceiling is {profile.carb_ceiling}g. Recommend reducing to {proposed_carb}g after approval.",
                    confidence_level=0.82,
                    data_used={"waist_recent_avg_cm": waist_recent, "waist_previous_avg_cm": waist_previous, "carb_ceiling_current_g": profile.carb_ceiling},
                    threshold_triggered="Waist not reducing AND carb ceiling > 80g.",
                    historical_comparison=f"Waist average comparison: recent={waist_recent}, previous={waist_previous}.",
                )
            )

        if strength_rising and waist_recent is not None and waist_previous is not None and abs(waist_recent - waist_previous) <= 0.4:
            weekly_recommendations.append(
                AgentRecommendation(
                    recommendation_type="weekly_refeed_allowance",
                    title="Allow 1 controlled refeed meal",
                    summary="Strength is rising while waist is stable. Allow 1 controlled refeed meal this week.",
                    confidence_level=0.78,
                    data_used={"strength_recent": strength_recent, "strength_previous": strength_previous, "waist_recent_avg_cm": waist_recent, "waist_previous_avg_cm": waist_previous},
                    threshold_triggered="Strength rising AND waist stable.",
                    historical_comparison=(
                        f"Strength index delta={round(strength_recent - strength_previous, 2)}, "
                        f"waist delta={round(waist_recent - waist_previous, 2)}cm."
                    ),
                )
            )

        if waist_not_reducing and fruit_frequency >= 6:
            state.fruit_allowance_current = 0
            state.fruit_allowance_weekly = 3
            weekly_recommendations.append(
                AgentRecommendation(
                    recommendation_type="weekly_fruit_allowance_reduction",
                    title="Reduce fruit allowance",
                    summary="Waist trend is rising with near-daily fruit intake. Reduce fruit allowance to 3 servings/week.",
                    confidence_level=0.86,
                    data_used={"waist_recent_avg_cm": waist_recent, "waist_previous_avg_cm": waist_previous, "fruit_days": fruit_frequency},
                    threshold_triggered="Waist increasing AND fruit logged daily.",
                    historical_comparison=f"fruit_days={fruit_frequency}/7 with non-improving waist trend.",
                )
            )

        if hdl_support_days >= 4:
            weekly_recommendations.append(
                AgentRecommendation(
                    recommendation_type="weekly_hdl_support_consistency",
                    title="HDL support consistent",
                    summary="Nuts intake plus strength sessions were consistent this week.",
                    confidence_level=0.75,
                    data_used={"hdl_support_days": hdl_support_days},
                    threshold_triggered="HDL-support days (nuts + strength) high.",
                    historical_comparison=f"HDL-support days this week: {hdl_support_days}/7.",
                )
            )

        if hdl_improving:
            state.fruit_allowance_weekly = min(9, state.fruit_allowance_weekly + 2)
            weekly_recommendations.append(
                AgentRecommendation(
                    recommendation_type="weekly_fruit_allowance_bonus",
                    title="Add 2 fruit servings this week",
                    summary="HDL is improving, so controlled fruit allowance is expanded by 2 servings/week.",
                    confidence_level=0.74,
                    data_used={"hdl_recent": hdl_recent, "hdl_previous": hdl_previous},
                    threshold_triggered="HDL improving week-over-week.",
                    historical_comparison=f"HDL moved from {hdl_previous} to {hdl_recent}.",
                )
            )

        state.last_weekly_scan = datetime.utcnow()
        state.notes = (
            f"Weekly scan {start_day}..{end_day}: rhr={rhr_recent}, sleep={sleep_recent}, fruit_days={fruit_frequency}, "
            f"oil_avg_tsp={oil_average}, image_restaurant_freq={restaurant_frequency}"
        )

        for rec in weekly_recommendations:
            self._create_pending_recommendation(db, user_id, AgentRunCadence.WEEKLY, rec)

        return True

    def run_monthly_review(self, db: Session, user_id: int) -> bool:
        user = db.get(User, user_id)
        if not user:
            return False

        state = self._get_or_create_agent_state(db, user)
        end_day = datetime.utcnow().date()
        start_day = end_day - timedelta(days=29)

        avg_insulin = self._average_insulin(db, user_id, start_day, end_day)
        avg_strength = self._strength_index(db, user_id, start_day, end_day)
        waist_start = self._average_waist(db, user_id, start_day, start_day + timedelta(days=6))
        waist_end = self._average_waist(db, user_id, end_day - timedelta(days=6), end_day)
        waist_reduction = None if waist_start is None or waist_end is None else round(waist_start - waist_end, 2)

        fasting_compliance = self._fasting_compliance_ratio(db, user_id, start_day, end_day)
        habit_compliance = self._habit_compliance_ratio(db, user_id, start_day, end_day)

        risk_classification = self._risk_classification(avg_insulin, fasting_compliance, habit_compliance)
        carb_phase = self._carb_phase(avg_insulin)
        strength_phase = self._strength_phase(avg_strength)
        hydration_improvement = self._hydration_improvement_text(db, user_id, start_day, end_day)

        monthly_report = {
            "report_type": "Monthly Metabolic Report",
            "window": {"start": str(start_day), "end": str(end_day)},
            "scores": {
                "average_insulin_score": avg_insulin,
                "average_strength_score": avg_strength,
                "waist_reduction_cm": waist_reduction,
                "habit_compliance_ratio": habit_compliance,
                "fasting_compliance_ratio": fasting_compliance,
            },
            "classification": {
                "risk_classification": risk_classification,
                "suggested_carb_tolerance_phase": carb_phase,
                "suggested_strength_progression_phase": strength_phase,
                "suggested_hydration_improvements": hydration_improvement,
            },
        }

        monthly_recommendation = AgentRecommendation(
            recommendation_type="monthly_metabolic_report",
            title="Monthly Metabolic Report ready",
            summary="Your monthly deterministic metabolic review is available for approval and coaching follow-up.",
            confidence_level=0.9,
            data_used=monthly_report,
            threshold_triggered="Monthly macro-evaluation completed.",
            historical_comparison=(
                f"Waist change over month={waist_reduction}cm, average insulin={avg_insulin}, average strength={avg_strength}."
            ),
        )

        self._create_pending_recommendation(db, user_id, AgentRunCadence.MONTHLY, monthly_recommendation)
        state.last_monthly_review = datetime.utcnow()
        state.notes = json.dumps(monthly_report)
        return True

    def build_weekly_report_payload(self, db: Session, user_id: int) -> dict:
        end_day = datetime.utcnow().date()
        start_day = end_day - timedelta(days=6)
        previous_start = start_day - timedelta(days=7)
        previous_end = start_day - timedelta(days=1)
        return {
            "report_type": "weekly_metabolic_analysis",
            "window": {"start": str(start_day), "end": str(end_day)},
            "metrics": {
                "waist_recent_avg_cm": self._average_waist(db, user_id, start_day, end_day),
                "waist_previous_avg_cm": self._average_waist(db, user_id, previous_start, previous_end),
                "strength_recent_index": self._strength_index(db, user_id, start_day, end_day),
                "strength_previous_index": self._strength_index(db, user_id, previous_start, previous_end),
                "resting_hr_recent": self._avg_vitals_metric(db, user_id, start_day, end_day, VitalsEntry.resting_hr),
                "sleep_recent_hours": self._avg_vitals_metric(db, user_id, start_day, end_day, VitalsEntry.sleep_hours),
                "fruit_days": self._fruit_frequency(db, user_id, start_day, end_day),
                "oil_avg_daily_tsp": self._avg_daily_oil(db, user_id, start_day, end_day),
                "image_detected_restaurant_frequency": self._restaurant_image_frequency(db, user_id, start_day, end_day),
            },
            "recommendation_logic": {
                "carb_reduction_rule": "If waist not reducing AND carb ceiling > 80, recommend -10g carb ceiling (pending approval).",
                "refeed_rule": "If strength rising AND waist stable, allow 1 controlled refeed meal.",
                "hdl_support_rule": "If nuts + strength days are high, mark HDL support consistent.",
            },
        }

    def summarize_weekly_analysis(self, structured_payload: dict) -> str | None:
        return llm_service.summarize_metabolic_agent_weekly_analysis(structured_payload)

    def _create_pending_recommendation(
        self,
        db: Session,
        user_id: int,
        cadence: AgentRunCadence,
        rec: AgentRecommendation,
    ) -> PendingRecommendation:
        llm_summary = llm_service.summarize_metabolic_agent_weekly_analysis(
            {
                "recommendation": {
                    "type": rec.recommendation_type,
                    "title": rec.title,
                    "summary": rec.summary,
                    "data_used": rec.data_used,
                },
                "guardrail": "LLM summarizes deterministic output only; no new rules.",
            }
        )
        pending = PendingRecommendation(
            user_id=user_id,
            cadence=cadence,
            recommendation_type=rec.recommendation_type,
            title=rec.title,
            summary=rec.summary,
            confidence_level=rec.confidence_level,
            data_used=json.dumps(rec.data_used),
            threshold_triggered=rec.threshold_triggered,
            historical_comparison=rec.historical_comparison,
            llm_summary=llm_summary,
        )
        db.add(pending)
        return pending


    @staticmethod
    def _has_consecutive_days(days: list[date]) -> bool:
        if len(days) < 2:
            return False
        ordered = sorted(days)
        for idx in range(1, len(ordered)):
            if (ordered[idx] - ordered[idx - 1]).days == 1:
                return True
        return False

    @staticmethod
    def _daily_insulin_map(db: Session, user_id: int, start_day: date, end_day: date) -> list[tuple[str, float]]:
        rows = db.execute(
            select(DailyLog.log_date, func.avg(InsulinScore.score))
            .join(InsulinScore, InsulinScore.daily_log_id == DailyLog.id)
            .where(
                DailyLog.user_id == user_id,
                DailyLog.log_date >= start_day,
                DailyLog.log_date <= end_day,
            )
            .group_by(DailyLog.log_date)
            .order_by(DailyLog.log_date)
        ).all()
        return [(str(day), round(float(score), 2)) for day, score in rows]

    @staticmethod
    def _count_fasting_violations(db: Session, user_id: int, start_day: date, end_day: date, profile: MetabolicProfile) -> int:
        entries = db.scalars(
            select(MealEntry)
            .join(DailyLog, DailyLog.id == MealEntry.daily_log_id)
            .where(
                DailyLog.user_id == user_id,
                DailyLog.log_date >= start_day,
                DailyLog.log_date <= end_day,
            )
        ).all()
        start_t = datetime.strptime(profile.fasting_start_time, "%H:%M").time()
        end_t = datetime.strptime(profile.fasting_end_time, "%H:%M").time()
        violations = 0
        for entry in entries:
            consumed = entry.consumed_at.time()
            if start_t > end_t:
                if consumed >= start_t or consumed < end_t:
                    violations += 1
            else:
                if start_t <= consumed < end_t:
                    violations += 1
        return violations

    @staticmethod
    def _hydration_compliance(db: Session, user_id: int, start_day: date, end_day: date) -> float:
        hydration_habit = db.scalar(select(HabitDefinition).where(HabitDefinition.code.in_(["hydration", "water_goal"])))
        if not hydration_habit:
            return 0.0
        checkins = db.scalars(
            select(HabitCheckin.success).where(
                HabitCheckin.user_id == user_id,
                HabitCheckin.habit_id == hydration_habit.id,
                HabitCheckin.habit_date >= start_day,
                HabitCheckin.habit_date <= end_day,
            )
        ).all()
        if not checkins:
            return 0.0
        successes = sum(1 for c in checkins if c)
        return round(successes / len(checkins), 2)

    @staticmethod
    def _strength_sessions(db: Session, user_id: int, start_day: date, end_day: date) -> int:
        strength_categories = [ExerciseCategory.STRENGTH, ExerciseCategory.BODYWEIGHT, ExerciseCategory.MONKEY_BAR]
        return len(
            db.scalars(
                select(ExerciseEntry.id).where(
                    ExerciseEntry.user_id == user_id,
                    ExerciseEntry.exercise_category.in_(strength_categories),
                    ExerciseEntry.performed_at >= datetime.combine(start_day, time.min),
                    ExerciseEntry.performed_at <= datetime.combine(end_day, time.max),
                )
            ).all()
        )

    @staticmethod
    def _average_waist(db: Session, user_id: int, start_day: date, end_day: date) -> float | None:
        rows = db.scalars(
            select(VitalsEntry.waist_cm).where(
                VitalsEntry.user_id == user_id,
                VitalsEntry.recorded_at >= datetime.combine(start_day, time.min),
                VitalsEntry.recorded_at <= datetime.combine(end_day, time.max),
                VitalsEntry.waist_cm.is_not(None),
            )
        ).all()
        if not rows:
            return None
        return round(sum(float(v) for v in rows) / len(rows), 2)

    @staticmethod
    def _strength_index(db: Session, user_id: int, start_day: date, end_day: date) -> float:
        entries = db.scalars(
            select(ExerciseEntry).where(
                ExerciseEntry.user_id == user_id,
                ExerciseEntry.performed_at >= datetime.combine(start_day, time.min),
                ExerciseEntry.performed_at <= datetime.combine(end_day, time.max),
            )
        ).all()
        return float(compute_strength_score(entries)["strength_index"])

    @staticmethod
    def _avg_vitals_metric(db: Session, user_id: int, start_day: date, end_day: date, column) -> float | None:
        rows = db.scalars(
            select(column).where(
                VitalsEntry.user_id == user_id,
                VitalsEntry.recorded_at >= datetime.combine(start_day, time.min),
                VitalsEntry.recorded_at <= datetime.combine(end_day, time.max),
                column.is_not(None),
            )
        ).all()
        if not rows:
            return None
        return round(sum(float(v) for v in rows) / len(rows), 2)

    @staticmethod
    def _fruit_frequency(db: Session, user_id: int, start_day: date, end_day: date) -> int:
        days = db.scalars(
            select(DailyLog.log_date)
            .join(MealEntry, MealEntry.daily_log_id == DailyLog.id)
            .join(FoodItem, FoodItem.id == MealEntry.food_item_id)
            .where(
                DailyLog.user_id == user_id,
                DailyLog.log_date >= start_day,
                DailyLog.log_date <= end_day,
                FoodItem.food_group == "fruit",
            )
            .distinct()
        ).all()
        return len(days)

    @staticmethod
    def _avg_daily_oil(db: Session, user_id: int, start_day: date, end_day: date) -> float | None:
        rows = db.scalars(
            select(DailyLog.total_hidden_oil).where(
                DailyLog.user_id == user_id,
                DailyLog.log_date >= start_day,
                DailyLog.log_date <= end_day,
            )
        ).all()
        if not rows:
            return None
        return round(sum(float(v) for v in rows) / len(rows), 2)

    @staticmethod
    def _restaurant_image_frequency(db: Session, user_id: int, start_day: date, end_day: date) -> int:
        entries = db.scalars(
            select(MealEntry.id)
            .join(DailyLog, DailyLog.id == MealEntry.daily_log_id)
            .where(
                DailyLog.user_id == user_id,
                DailyLog.log_date >= start_day,
                DailyLog.log_date <= end_day,
                MealEntry.image_url.is_not(None),
                MealEntry.vision_confidence.is_not(None),
                MealEntry.vision_confidence >= 0.6,
            )
        ).all()
        return len(entries)

    @staticmethod
    def _hdl_support_days(db: Session, user_id: int, start_day: date, end_day: date) -> int:
        strength_days = {
            performed.date()
            for performed in db.scalars(
                select(ExerciseEntry.performed_at).where(
                    ExerciseEntry.user_id == user_id,
                    ExerciseEntry.performed_at >= datetime.combine(start_day, time.min),
                    ExerciseEntry.performed_at <= datetime.combine(end_day, time.max),
                    ExerciseEntry.exercise_category.in_([ExerciseCategory.STRENGTH, ExerciseCategory.BODYWEIGHT, ExerciseCategory.MONKEY_BAR]),
                )
            ).all()
        }
        nuts_days = {
            day
            for day in db.scalars(
                select(DailyLog.log_date)
                .join(MealEntry, MealEntry.daily_log_id == DailyLog.id)
                .join(FoodItem, FoodItem.id == MealEntry.food_item_id)
                .where(
                    DailyLog.user_id == user_id,
                    DailyLog.log_date >= start_day,
                    DailyLog.log_date <= end_day,
                    FoodItem.food_group == "nut",
                )
                .distinct()
            ).all()
        }
        return len(strength_days.intersection(nuts_days))

    @staticmethod
    def _average_insulin(db: Session, user_id: int, start_day: date, end_day: date) -> float | None:
        rows = db.scalars(
            select(InsulinScore.score)
            .join(DailyLog, DailyLog.id == InsulinScore.daily_log_id)
            .where(
                DailyLog.user_id == user_id,
                DailyLog.log_date >= start_day,
                DailyLog.log_date <= end_day,
            )
        ).all()
        if not rows:
            return None
        return round(sum(float(v) for v in rows) / len(rows), 2)

    @staticmethod
    def _fasting_compliance_ratio(db: Session, user_id: int, start_day: date, end_day: date) -> float:
        profile = db.scalar(select(MetabolicProfile).where(MetabolicProfile.user_id == user_id))
        if not profile:
            return 0.0
        total_entries = db.scalars(
            select(MealEntry)
            .join(DailyLog, DailyLog.id == MealEntry.daily_log_id)
            .where(
                DailyLog.user_id == user_id,
                DailyLog.log_date >= start_day,
                DailyLog.log_date <= end_day,
            )
        ).all()
        if not total_entries:
            return 0.0
        violations = MetabolicAgentService._count_fasting_violations(db, user_id, start_day, end_day, profile)
        return round(max(0.0, 1 - (violations / len(total_entries))), 2)

    @staticmethod
    def _habit_compliance_ratio(db: Session, user_id: int, start_day: date, end_day: date) -> float:
        checkins = db.scalars(
            select(HabitCheckin.success).where(
                HabitCheckin.user_id == user_id,
                HabitCheckin.habit_date >= start_day,
                HabitCheckin.habit_date <= end_day,
            )
        ).all()
        if not checkins:
            return 0.0
        success = sum(1 for c in checkins if c)
        return round(success / len(checkins), 2)

    @staticmethod
    def _risk_classification(avg_insulin: float | None, fasting_compliance: float, habit_compliance: float) -> str:
        insulin = avg_insulin if avg_insulin is not None else 100.0
        if insulin < 45 and fasting_compliance >= 0.8 and habit_compliance >= 0.75:
            return "Low"
        if insulin < 70 and fasting_compliance >= 0.6 and habit_compliance >= 0.5:
            return "Moderate"
        return "Elevated"

    @staticmethod
    def _carb_phase(avg_insulin: float | None) -> str:
        if avg_insulin is None:
            return "Assessment phase"
        if avg_insulin <= 45:
            return "Carb tolerance expansion"
        if avg_insulin <= 70:
            return "Controlled carb maintenance"
        return "Carb tightening"

    @staticmethod
    def _strength_phase(avg_strength: float) -> str:
        if avg_strength >= 45:
            return "Progressive overload"
        if avg_strength >= 20:
            return "Base strength consolidation"
        return "Foundational activation"

    @staticmethod
    def _hydration_improvement_text(db: Session, user_id: int, start_day: date, end_day: date) -> str:
        compliance = MetabolicAgentService._hydration_compliance(db, user_id, start_day, end_day)
        if compliance >= 0.8:
            return "Hydration habits are strong; maintain current approach."
        if compliance > 0:
            return "Set fixed hydration checkpoints (wake-up, post-workout, evening)."
        return "Hydration tracking is missing; add a daily hydration check-in habit."

    @staticmethod
    def _get_or_create_profile(db: Session, user: User) -> MetabolicProfile:
        profile = db.scalar(select(MetabolicProfile).where(MetabolicProfile.user_id == user.id))
        if profile:
            return profile
        profile = MetabolicProfile(
            user_id=user.id,
            protein_target_min=user.protein_target_min,
            protein_target_max=user.protein_target_max,
            carb_ceiling=user.carb_ceiling,
            oil_limit_tsp=user.oil_limit_tsp,
        )
        db.add(profile)
        db.flush()
        return profile

    @staticmethod
    def _get_or_create_agent_state(db: Session, user: User) -> MetabolicAgentState:
        state = db.get(MetabolicAgentState, user.id)
        if state:
            return state
        state = MetabolicAgentState(
            user_id=user.id,
            carb_ceiling_current=user.carb_ceiling,
            protein_target_current=user.protein_target_min,
            fruit_allowance_current=1,
            fruit_allowance_weekly=7,
            notes="Initialized on first agent run.",
        )
        db.add(state)
        db.flush()
        return state


metabolic_agent_service = MetabolicAgentService()
