from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from random import choices

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ChallengeAssignment, ChallengeFrequency, ChallengeStreak, DailyLog, ExerciseCategory, ExerciseEntry, User, VitalsEntry
from app.services.rule_engine import get_or_create_metabolic_profile


@dataclass(frozen=True)
class ChallengeTemplate:
    code: str
    name: str
    description: str
    metric: str
    target_value: float


DAILY_TEMPLATES = {
    "no_carb_dinner_day": ChallengeTemplate(
        code="no_carb_dinner_day",
        name="No Carb Dinner Day",
        description="Keep dinner carbs near-zero and prioritize non-starchy vegetables + protein.",
        metric="dinner_carbs",
        target_value=10,
    ),
    "protein_first_day": ChallengeTemplate(
        code="protein_first_day",
        name="Protein First Day",
        description="Start each major meal with protein to blunt insulin spikes.",
        metric="protein_first_meals",
        target_value=3,
    ),
    "step_10k_day": ChallengeTemplate(
        code="step_10k_day",
        name="10k Step Day",
        description="Reach at least 10,000 steps through walks and movement snacks.",
        metric="steps",
        target_value=10_000,
    ),
    "monkey_bar_hold_60": ChallengeTemplate(
        code="monkey_bar_hold_60",
        name="Monkey Bar Hold 60 Seconds",
        description="Accumulate a total of 60 seconds of monkey bar or dead-hang holds.",
        metric="dead_hang_seconds",
        target_value=60,
    ),
    "oil_under_2_tsp": ChallengeTemplate(
        code="oil_under_2_tsp",
        name="Oil Under 2 tsp Day",
        description="Keep hidden cooking oil intake under 2 teaspoons.",
        metric="hidden_oil_tsp",
        target_value=2,
    ),
}

MONTHLY_TEMPLATES = {
    "step_10k_day": ChallengeTemplate(
        code="step_10k_day",
        name="10k Step Day",
        description="Complete at least 20 days with 10k+ steps this month.",
        metric="days_over_10k",
        target_value=20,
    ),
    "protein_first_day": ChallengeTemplate(
        code="protein_first_day",
        name="Protein First Day",
        description="Hit protein-first eating on 25 days this month.",
        metric="protein_first_days",
        target_value=25,
    ),
    "oil_under_2_tsp": ChallengeTemplate(
        code="oil_under_2_tsp",
        name="Oil Under 2 tsp Day",
        description="Stay below 2 tsp hidden oil for 24 days this month.",
        metric="low_oil_days",
        target_value=24,
    ),
}


class ChallengeEngine:
    def __init__(self, db: Session):
        self.db = db

    def assign_for_today(self, user: User, frequency: ChallengeFrequency = ChallengeFrequency.DAILY) -> ChallengeAssignment:
        today = datetime.utcnow().date()

        if frequency == ChallengeFrequency.MONTHLY:
            period_start = today.replace(day=1)
            next_month = (period_start.replace(day=28) + timedelta(days=4)).replace(day=1)
            period_end = next_month - timedelta(days=1)
            existing = self.db.scalar(
                select(ChallengeAssignment).where(
                    ChallengeAssignment.user_id == user.id,
                    ChallengeAssignment.frequency == frequency,
                    ChallengeAssignment.period_start == period_start,
                )
            )
            if existing:
                return existing
        else:
            period_start = period_end = today
            existing = self.db.scalar(
                select(ChallengeAssignment).where(
                    ChallengeAssignment.user_id == user.id,
                    ChallengeAssignment.frequency == frequency,
                    ChallengeAssignment.challenge_date == today,
                )
            )
            if existing:
                return existing

        template = self._select_template(user, frequency)
        assignment = ChallengeAssignment(
            user_id=user.id,
            frequency=frequency,
            challenge_date=today,
            period_start=period_start,
            period_end=period_end,
            challenge_code=template.code,
            challenge_name=template.name,
            challenge_description=template.description,
            goal_metric=template.metric,
            goal_target=template.target_value,
        )
        self.db.add(assignment)
        self.db.flush()
        return assignment

    def mark_completed(self, assignment: ChallengeAssignment) -> ChallengeStreak:
        if assignment.completed:
            return self.get_or_create_streak(assignment.user_id, assignment.frequency)

        assignment.completed = True
        assignment.completed_at = datetime.utcnow()

        streak = self.get_or_create_streak(assignment.user_id, assignment.frequency)
        completion_date = assignment.challenge_date
        if streak.last_completed_on == completion_date - timedelta(days=1):
            streak.current_streak += 1
        elif streak.last_completed_on == completion_date:
            return streak
        else:
            streak.current_streak = 1

        streak.last_completed_on = completion_date
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        return streak

    def _select_template(self, user: User, frequency: ChallengeFrequency) -> ChallengeTemplate:
        templates = MONTHLY_TEMPLATES if frequency == ChallengeFrequency.MONTHLY else DAILY_TEMPLATES
        weights = self._weakness_weights(user, templates)
        weighted_codes = list(weights.keys())
        return templates[choices(weighted_codes, weights=list(weights.values()), k=1)[0]]

    def _weakness_weights(self, user: User, templates: dict[str, ChallengeTemplate]) -> dict[str, float]:
        profile = get_or_create_metabolic_profile(self.db, user)
        recent_logs = self.db.scalars(
            select(DailyLog)
            .where(DailyLog.user_id == user.id)
            .order_by(DailyLog.log_date.desc())
            .limit(7)
        ).all()
        recent_vitals = self.db.scalars(
            select(VitalsEntry)
            .where(VitalsEntry.user_id == user.id)
            .order_by(VitalsEntry.recorded_at.desc())
            .limit(7)
        ).all()

        avg_carbs = sum(log.total_carbs for log in recent_logs) / len(recent_logs) if recent_logs else profile.carb_ceiling
        avg_protein = sum(log.total_protein for log in recent_logs) / len(recent_logs) if recent_logs else profile.protein_target_min
        avg_oil = sum(log.total_hidden_oil for log in recent_logs) / len(recent_logs) if recent_logs else profile.oil_limit_tsp
        avg_steps = sum(v.steps_total for v in recent_vitals) / len(recent_vitals) if recent_vitals else 0

        monkey_seconds = self.db.scalar(
            select(func.max(ExerciseEntry.dead_hang_duration_seconds)).where(
                ExerciseEntry.user_id == user.id,
                ExerciseEntry.exercise_category == ExerciseCategory.MONKEY_BAR,
            )
        ) or 0

        base_weights = {code: 1.0 for code in templates.keys()}
        if "no_carb_dinner_day" in base_weights:
            base_weights["no_carb_dinner_day"] += max(0.0, (avg_carbs - profile.carb_ceiling) / 10)
        if "protein_first_day" in base_weights:
            base_weights["protein_first_day"] += max(0.0, (profile.protein_target_min - avg_protein) / 10)
        if "step_10k_day" in base_weights:
            base_weights["step_10k_day"] += max(0.0, (10_000 - avg_steps) / 2_500)
        if "monkey_bar_hold_60" in base_weights:
            base_weights["monkey_bar_hold_60"] += max(0.0, (60 - monkey_seconds) / 20)
        if "oil_under_2_tsp" in base_weights:
            base_weights["oil_under_2_tsp"] += max(0.0, (avg_oil - 2) / 0.5)

        return base_weights

    def get_or_create_streak(self, user_id: int, frequency: ChallengeFrequency) -> ChallengeStreak:
        streak = self.db.scalar(
            select(ChallengeStreak).where(ChallengeStreak.user_id == user_id, ChallengeStreak.frequency == frequency)
        )
        if streak:
            return streak

        streak = ChallengeStreak(user_id=user_id, frequency=frequency)
        self.db.add(streak)
        self.db.flush()
        return streak
