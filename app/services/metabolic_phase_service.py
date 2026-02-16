from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    DailyLog,
    ExerciseCategory,
    ExerciseEntry,
    InsulinScore,
    MetabolicAgentState,
    MetabolicPhase,
    User,
    VitalsEntry,
)
from app.services.strength_engine import compute_strength_score


PHASE_RULES: dict[MetabolicPhase, dict] = {
    MetabolicPhase.RESET: {
        "carb_ceiling": "80-90g",
        "rice_rule": "No rice",
        "fruit_rule": "Strict fruit limit",
        "strength_rule": "Strength 3x/week minimum",
        "identity": "Repair Mode",
    },
    MetabolicPhase.STABILIZATION: {
        "carb_ceiling": "90-110g",
        "rice_rule": "1 rice meal per week allowed",
        "fruit_rule": "Moderate fruit limit",
        "strength_rule": "Strength progressive overload",
        "identity": "Control Mode",
    },
    MetabolicPhase.RECOMPOSITION: {
        "carb_ceiling": "Carb cycling",
        "rice_rule": "Controlled carb cycling days",
        "fruit_rule": "Fruit tied to training days",
        "strength_rule": "Strength 4x/week + monkey bar progression",
        "identity": "Rebuild Mode",
    },
    MetabolicPhase.PERFORMANCE: {
        "carb_ceiling": "Adaptive",
        "rice_rule": "2 refeed meals allowed",
        "fruit_rule": "Fuel-performance alignment",
        "strength_rule": "Strength index primary metric",
        "identity": "Elite Mode",
    },
    MetabolicPhase.MAINTENANCE: {
        "carb_ceiling": "Adaptive maintenance",
        "rice_rule": "Flexible structured meals",
        "fruit_rule": "Stable tolerance range",
        "strength_rule": "Strength retention",
        "identity": "Sustain Mode",
    },
}


class MetabolicPhaseService:
    def build_phase_dashboard(self, db: Session, user_id: int) -> dict | None:
        user = db.get(User, user_id)
        if not user:
            return None

        state = self._get_or_create_state(db, user_id)
        phase_decision = self._evaluate_phase_transition(db, user_id, state.metabolic_phase)
        if phase_decision["should_transition"]:
            state.metabolic_phase = phase_decision["target_phase"]
            state.metabolic_identity = PHASE_RULES[state.metabolic_phase]["identity"]

        carb_tolerance = self._build_carb_tolerance_index(db, user_id)
        periodization = self._build_periodization(db, user_id)
        performance = self._build_performance_metrics(db, user_id, carb_tolerance["carb_tolerance_index"])

        state.notes = (
            f"phase={state.metabolic_phase.value}, transition={phase_decision['reason']}, "
            f"carb_tolerance_index={carb_tolerance['carb_tolerance_index']:.1f}"
        )
        db.flush()

        return {
            "phase_model": {
                "current_phase": state.metabolic_phase,
                "identity": state.metabolic_identity,
                "rules": PHASE_RULES[state.metabolic_phase],
                "all_phases": [
                    {
                        "phase": phase,
                        "identity": PHASE_RULES[phase]["identity"],
                        "carb_ceiling": PHASE_RULES[phase]["carb_ceiling"],
                        "strength_rule": PHASE_RULES[phase]["strength_rule"],
                    }
                    for phase in MetabolicPhase
                ],
            },
            "transition_logic": phase_decision,
            "carb_tolerance": carb_tolerance,
            "performance_dashboard": performance,
            "periodization": periodization,
            "example_transition_scenario": self._example_transition_scenario(),
            "backend_logic": {
                "phase_transition_source": "Waist trend + insulin average + strength + resting HR",
                "carb_challenge_source": "Controlled rice meal + next-day vitals",
                "periodization_source": "Monthly 4-week strength cycle",
            },
        }

    def _get_or_create_state(self, db: Session, user_id: int) -> MetabolicAgentState:
        state = db.get(MetabolicAgentState, user_id)
        if state:
            return state
        state = MetabolicAgentState(user_id=user_id)
        db.add(state)
        db.flush()
        return state

    def _evaluate_phase_transition(self, db: Session, user_id: int, current: MetabolicPhase) -> dict:
        today = datetime.utcnow().date()
        start_28 = today - timedelta(days=27)
        start_14 = today - timedelta(days=13)

        waist_entries = db.scalars(
            select(VitalsEntry)
            .where(
                VitalsEntry.user_id == user_id,
                VitalsEntry.recorded_at >= datetime.combine(start_28, datetime.min.time()),
            )
            .order_by(VitalsEntry.recorded_at.asc())
        ).all()

        insulin_rows = db.scalars(
            select(InsulinScore.score)
            .join(DailyLog, DailyLog.id == InsulinScore.daily_log_id)
            .where(DailyLog.user_id == user_id, DailyLog.log_date >= start_14)
        ).all()

        strength_recent = self._strength_index(db, user_id, start_14, today)
        strength_previous = self._strength_index(db, user_id, start_14 - timedelta(days=14), start_14 - timedelta(days=1))

        rhr_recent = self._avg_rhr(db, user_id, start_14, today)
        rhr_prev = self._avg_rhr(db, user_id, start_14 - timedelta(days=14), start_14 - timedelta(days=1))

        waist_4_week_drop = self._waist_drop_four_weeks(waist_entries)
        waist_stable = self._waist_stable(waist_entries)
        insulin_avg = round(sum(insulin_rows) / len(insulin_rows), 2) if insulin_rows else 100.0
        strength_rising = strength_recent > strength_previous
        rhr_improved = rhr_recent is not None and rhr_prev is not None and rhr_recent < rhr_prev

        should_transition = False
        target_phase = current
        reason = "Conditions not met"

        if current == MetabolicPhase.RESET:
            if waist_4_week_drop and insulin_avg < 50 and strength_rising:
                should_transition = True
                target_phase = MetabolicPhase.STABILIZATION
                reason = "RESET → STABILIZATION: waist reduced 4 consecutive weeks, insulin < 50, strength trending upward"
        elif current == MetabolicPhase.STABILIZATION:
            if waist_stable and strength_rising and rhr_improved:
                should_transition = True
                target_phase = MetabolicPhase.RECOMPOSITION
                reason = "STABILIZATION → RECOMPOSITION: waist stable, strength rising, resting HR improved"

        return {
            "should_transition": should_transition,
            "current_phase": current,
            "target_phase": target_phase,
            "reason": reason,
            "signals": {
                "waist_4_week_drop": waist_4_week_drop,
                "waist_stable": waist_stable,
                "insulin_average": insulin_avg,
                "strength_rising": strength_rising,
                "resting_hr_improved": rhr_improved,
            },
        }

    def _build_carb_tolerance_index(self, db: Session, user_id: int) -> dict:
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        today = datetime.utcnow().date()
        rice_meal = db.scalar(
            select(ExerciseEntry)
            .where(
                ExerciseEntry.user_id == user_id,
                ExerciseEntry.activity_type == "CARB_CHALLENGE_DAY",
                ExerciseEntry.performed_at >= datetime.combine(yesterday, datetime.min.time()),
                ExerciseEntry.performed_at < datetime.combine(today, datetime.min.time()),
            )
            .order_by(ExerciseEntry.performed_at.desc())
        )

        insulin_next_day = db.scalar(
            select(InsulinScore.score)
            .join(DailyLog, DailyLog.id == InsulinScore.daily_log_id)
            .where(DailyLog.user_id == user_id, DailyLog.log_date == today)
            .order_by(InsulinScore.calculated_at.desc())
        )

        vitals_next_day = db.scalar(
            select(VitalsEntry)
            .where(
                VitalsEntry.user_id == user_id,
                VitalsEntry.recorded_at >= datetime.combine(today, datetime.min.time()),
            )
            .order_by(VitalsEntry.recorded_at.desc())
        )

        energy_level = 7.0
        if vitals_next_day and vitals_next_day.hrv is not None:
            energy_level = min(10.0, max(1.0, vitals_next_day.hrv / 10))

        insulin_component = 100 - float(insulin_next_day or 70)
        sleep_component = min(100.0, float(vitals_next_day.sleep_hours or 6) * 12.5) if vitals_next_day else 50.0
        rhr_component = 100 - min(40.0, float(vitals_next_day.resting_hr or 70) - 50) if vitals_next_day else 60.0
        energy_component = energy_level * 10

        carb_tolerance_index = round(max(0.0, min(100.0, (insulin_component * 0.45) + (energy_component * 0.2) + (sleep_component * 0.2) + (rhr_component * 0.15))), 2)

        return {
            "carb_challenge_day_logged": bool(rice_meal),
            "protocol": "1 controlled rice meal then next-day measurements",
            "next_day_metrics": {
                "insulin_score": insulin_next_day,
                "energy_level": round(energy_level, 2),
                "sleep_hours": float(vitals_next_day.sleep_hours) if vitals_next_day and vitals_next_day.sleep_hours is not None else None,
                "resting_hr": float(vitals_next_day.resting_hr) if vitals_next_day and vitals_next_day.resting_hr is not None else None,
            },
            "carb_tolerance_index": carb_tolerance_index,
            "evaluation": "Good tolerance" if carb_tolerance_index >= 70 else "Moderate tolerance" if carb_tolerance_index >= 50 else "Low tolerance",
        }

    def _build_performance_metrics(self, db: Session, user_id: int, carb_tolerance_index: float) -> dict:
        end = datetime.utcnow().date()
        start = end - timedelta(days=29)
        strength_index = self._strength_index(db, user_id, start, end)
        grip_sessions = db.scalars(
            select(ExerciseEntry.grip_intensity_score).where(
                ExerciseEntry.user_id == user_id,
                ExerciseEntry.performed_at >= datetime.combine(start, datetime.min.time()),
            )
        ).all()
        recovery_rows = db.scalars(
            select(VitalsEntry).where(
                VitalsEntry.user_id == user_id,
                VitalsEntry.recorded_at >= datetime.combine(start, datetime.min.time()),
            )
        ).all()
        avg_sleep = round(sum((row.sleep_hours or 0) for row in recovery_rows) / len(recovery_rows), 2) if recovery_rows else 0.0
        sleep_consistency = round(min(100.0, max(0.0, avg_sleep / 8 * 100)), 2)
        recovery_score = round(min(100.0, max(0.0, 100 - (sum((row.resting_hr or 72) for row in recovery_rows) / len(recovery_rows) - 55))), 2) if recovery_rows else 55.0

        return {
            "strength_index": round(strength_index, 2),
            "grip_score": round(sum(grip_sessions) / len(grip_sessions), 2) if grip_sessions else 0.0,
            "carb_tolerance_index": carb_tolerance_index,
            "recovery_score": recovery_score,
            "sleep_consistency": sleep_consistency,
        }

    def _build_periodization(self, db: Session, user_id: int) -> dict:
        now = datetime.utcnow().date()
        start = now - timedelta(days=27)
        sessions = db.scalars(
            select(ExerciseEntry)
            .where(ExerciseEntry.user_id == user_id, ExerciseEntry.performed_at >= datetime.combine(start, datetime.min.time()))
            .order_by(ExerciseEntry.performed_at.asc())
        ).all()

        weekly_blocks = [
            {"week": 1, "focus": "Base", "target": "Foundational strength volume"},
            {"week": 2, "focus": "Progressive overload", "target": "Add load/reps"},
            {"week": 3, "focus": "Intensity focus", "target": "Higher intensity lower volume"},
            {"week": 4, "focus": "Deload", "target": "Recover + maintain movement quality"},
        ]

        monkey_sessions = [s for s in sessions if s.exercise_category == ExerciseCategory.MONKEY_BAR]
        monkey_metrics = {
            "sessions": len(monkey_sessions),
            "best_dead_hang_seconds": max((s.dead_hang_duration_seconds or 0) for s in monkey_sessions) if monkey_sessions else 0,
            "best_pull_up_count": max((s.pull_up_count or 0) for s in monkey_sessions) if monkey_sessions else 0,
            "best_grip_endurance_seconds": max((s.grip_endurance_seconds or 0) for s in monkey_sessions) if monkey_sessions else 0,
        }

        return {
            "monthly_cycle": weekly_blocks,
            "monkey_bar_metrics": monkey_metrics,
        }

    def _strength_index(self, db: Session, user_id: int, start_day, end_day) -> float:
        entries = db.scalars(
            select(ExerciseEntry).where(
                ExerciseEntry.user_id == user_id,
                ExerciseEntry.performed_at >= datetime.combine(start_day, datetime.min.time()),
                ExerciseEntry.performed_at < datetime.combine(end_day + timedelta(days=1), datetime.min.time()),
            )
        ).all()
        return float(compute_strength_score(entries).strength_index)

    def _avg_rhr(self, db: Session, user_id: int, start_day, end_day) -> float | None:
        vitals = db.scalars(
            select(VitalsEntry.resting_hr).where(
                VitalsEntry.user_id == user_id,
                VitalsEntry.recorded_at >= datetime.combine(start_day, datetime.min.time()),
                VitalsEntry.recorded_at < datetime.combine(end_day + timedelta(days=1), datetime.min.time()),
                VitalsEntry.resting_hr.is_not(None),
            )
        ).all()
        if not vitals:
            return None
        return float(sum(vitals) / len(vitals))

    def _waist_drop_four_weeks(self, entries: list[VitalsEntry]) -> bool:
        weekly = []
        for week in range(4):
            block = [e.waist_cm for i, e in enumerate(entries) if e.waist_cm is not None and ((i // max(1, len(entries) // 4)) == week)]
            if not block:
                return False
            weekly.append(sum(block) / len(block))
        return weekly[0] > weekly[1] > weekly[2] > weekly[3]

    def _waist_stable(self, entries: list[VitalsEntry]) -> bool:
        values = [e.waist_cm for e in entries if e.waist_cm is not None]
        if len(values) < 2:
            return False
        return abs(values[-1] - values[0]) <= 0.8

    def _example_transition_scenario(self) -> dict:
        return {
            "starting_phase": "RESET",
            "signals": {
                "waist_4_week_trend": [-0.4, -0.5, -0.3, -0.4],
                "insulin_average": 46.2,
                "strength_index_delta": 6.8,
            },
            "outcome": "Transition to STABILIZATION",
            "next_constraints": {
                "carb_ceiling": "90-110g",
                "rice_meals": "1 per week",
                "identity": "Control Mode",
            },
        }


metabolic_phase_service = MetabolicPhaseService()
