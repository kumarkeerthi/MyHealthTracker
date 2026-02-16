from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import DailyLog, ExerciseCategory, ExerciseEntry, InsulinScore, MealEntry
from app.services.notification_service import notification_service

Sensitivity = Literal["strict", "balanced", "relaxed"]


@dataclass
class MovementSettingsSnapshot:
    reminder_delay_minutes: int = 45
    sensitivity: Sensitivity = "balanced"
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    max_alerts_per_day: int = 3


class MovementEngine:
    HIGH_INSULIN_THRESHOLD = 70

    def get_settings(self, db: Session, user_id: int) -> MovementSettingsSnapshot:
        settings = notification_service.get_or_create_settings(db, user_id)
        reminder_delay = int(getattr(settings, "movement_reminder_delay_minutes", 45) or 45)
        sensitivity = str(getattr(settings, "movement_sensitivity", "balanced") or "balanced").lower()
        if sensitivity not in {"strict", "balanced", "relaxed"}:
            sensitivity = "balanced"
        return MovementSettingsSnapshot(
            reminder_delay_minutes=max(15, min(90, reminder_delay)),
            sensitivity=sensitivity,
            quiet_hours_start=getattr(settings, "quiet_hours_start", None),
            quiet_hours_end=getattr(settings, "quiet_hours_end", None),
        )

    def update_settings(self, db: Session, user_id: int, payload: dict) -> MovementSettingsSnapshot:
        settings = notification_service.get_or_create_settings(db, user_id)
        if "reminder_delay_minutes" in payload and payload["reminder_delay_minutes"] is not None:
            settings.movement_reminder_delay_minutes = int(payload["reminder_delay_minutes"])
        if "sensitivity" in payload and payload["sensitivity"] is not None:
            settings.movement_sensitivity = str(payload["sensitivity"]).lower()
        if "quiet_hours_start" in payload:
            settings.quiet_hours_start = payload["quiet_hours_start"]
        if "quiet_hours_end" in payload:
            settings.quiet_hours_end = payload["quiet_hours_end"]
        db.flush()
        return self.get_settings(db, user_id)

    def _get_today_alert_count(self, db: Session, user_id: int, target_date: date) -> int:
        start_dt = datetime.combine(target_date, time.min)
        end_dt = datetime.combine(target_date, time.max)
        return int(
            db.scalar(
                select(func.count(ExerciseEntry.id)).where(
                    ExerciseEntry.user_id == user_id,
                    ExerciseEntry.activity_type == "movement_alert",
                    ExerciseEntry.performed_at >= start_dt,
                    ExerciseEntry.performed_at <= end_dt,
                )
            )
            or 0
        )

    def _track_alert(self, db: Session, user_id: int, alert_type: str, when: datetime) -> None:
        db.add(
            ExerciseEntry(
                user_id=user_id,
                daily_log_id=None,
                activity_type="movement_alert",
                exercise_category=ExerciseCategory.WALK,
                movement_type=alert_type,
                muscle_group="none",
                duration_minutes=1,
                perceived_intensity=1,
                calories_burned_estimate=0.0,
                post_meal_walk=False,
                performed_at=when,
            )
        )

    def _within_quiet_hours(self, quiet_start: str | None, quiet_end: str | None, now: datetime) -> bool:
        if not quiet_start or not quiet_end:
            return False
        start = datetime.strptime(quiet_start, "%H:%M").time()
        end = datetime.strptime(quiet_end, "%H:%M").time()
        now_time = now.time()
        if start <= end:
            return start <= now_time <= end
        return now_time >= start or now_time <= end

    def _send_alert(self, db: Session, user_id: int, title: str, body: str, alert_type: str, now: datetime, metadata: dict | None = None) -> dict:
        settings = self.get_settings(db, user_id)
        if self._within_quiet_hours(settings.quiet_hours_start, settings.quiet_hours_end, now):
            return {"status": "skipped", "reason": "quiet_hours"}
        if self._get_today_alert_count(db, user_id, now.date()) >= settings.max_alerts_per_day:
            return {"status": "skipped", "reason": "daily_limit"}
        result = notification_service.send_message(db, user_id, "push", title, body, metadata=metadata or {})
        if result.get("status") == "sent":
            self._track_alert(db, user_id, alert_type, now)
        return result

    def evaluate(self, db: Session, user_id: int, now: datetime | None = None) -> dict:
        current_time = now or datetime.utcnow()
        settings = self.get_settings(db, user_id)
        alerts: list[dict] = []
        penalties_applied = 0

        meal_window_start = current_time - timedelta(minutes=60)
        recent_meals = db.scalars(
            select(MealEntry)
            .join(DailyLog, DailyLog.id == MealEntry.daily_log_id)
            .where(
                DailyLog.user_id == user_id,
                MealEntry.consumed_at >= meal_window_start,
                MealEntry.consumed_at <= current_time,
            )
            .order_by(MealEntry.consumed_at.desc())
        ).all()

        for meal in recent_meals:
            reminder_due = meal.consumed_at + timedelta(minutes=settings.reminder_delay_minutes)
            if current_time < reminder_due:
                continue
            has_walk = db.scalar(
                select(func.count(ExerciseEntry.id)).where(
                    ExerciseEntry.user_id == user_id,
                    ExerciseEntry.performed_at >= meal.consumed_at,
                    ExerciseEntry.performed_at <= meal.consumed_at + timedelta(minutes=60),
                    or_(
                        ExerciseEntry.exercise_category == ExerciseCategory.WALK,
                        ExerciseEntry.post_meal_walk.is_(True),
                    ),
                )
            )
            if has_walk:
                continue
            alerts.append(
                self._send_alert(
                    db,
                    user_id,
                    title="Movement Reminder",
                    body="20 min walk now improves insulin control.",
                    alert_type="post_meal_walk_prompt",
                    now=current_time,
                    metadata={"meal_entry_id": meal.id},
                )
            )

            if current_time >= meal.consumed_at + timedelta(minutes=60):
                alerts.append(
                    self._send_alert(
                        db,
                        user_id,
                        title="Movement Follow-up",
                        body="Walking would have reduced impact.",
                        alert_type="post_meal_penalty_prompt",
                        now=current_time,
                        metadata={"meal_entry_id": meal.id, "penalty": 10},
                    )
                )
                penalties_applied += self._apply_penalty_if_high_carb_no_walk(db, meal)

        latest_insulin = db.scalar(
            select(InsulinScore)
            .join(DailyLog, DailyLog.id == InsulinScore.daily_log_id)
            .where(DailyLog.user_id == user_id)
            .order_by(InsulinScore.calculated_at.desc())
        )
        if latest_insulin and float(latest_insulin.score) > self.HIGH_INSULIN_THRESHOLD:
            alerts.append(
                self._send_alert(
                    db,
                    user_id,
                    title="Metabolic Alert",
                    body="High insulin load detected. Walk recommended within 30 minutes.",
                    alert_type="high_insulin_alert",
                    now=current_time,
                    metadata={"insulin_load_score": float(latest_insulin.score)},
                )
            )
            no_walk_after = db.scalar(
                select(func.count(ExerciseEntry.id)).where(
                    ExerciseEntry.user_id == user_id,
                    ExerciseEntry.performed_at >= latest_insulin.calculated_at,
                    ExerciseEntry.performed_at <= latest_insulin.calculated_at + timedelta(minutes=60),
                    or_(
                        ExerciseEntry.exercise_category == ExerciseCategory.WALK,
                        ExerciseEntry.post_meal_walk.is_(True),
                    ),
                )
            )
            if not no_walk_after and current_time >= latest_insulin.calculated_at + timedelta(minutes=60):
                alerts.append(
                    self._send_alert(
                        db,
                        user_id,
                        title="Gentle Reminder",
                        body="A short walk still helps—try 5 to 20 minutes now.",
                        alert_type="high_insulin_escalation",
                        now=current_time,
                    )
                )

        if 7 <= current_time.hour <= 22:
            latest_movement = db.scalar(
                select(ExerciseEntry.performed_at)
                .where(ExerciseEntry.user_id == user_id)
                .order_by(ExerciseEntry.performed_at.desc())
            )
            if (not latest_movement) or (current_time - latest_movement >= timedelta(hours=3)):
                alerts.append(
                    self._send_alert(
                        db,
                        user_id,
                        title="Movement Reset",
                        body="Movement reset — 5 minute walk.",
                        alert_type="inactivity_reset",
                        now=current_time,
                    )
                )

        return {"alerts": alerts, "penalties_applied": penalties_applied}

    def _apply_penalty_if_high_carb_no_walk(self, db: Session, meal: MealEntry) -> int:
        if meal.food_item is None:
            db.refresh(meal, ["food_item"])
        carb_total = float((meal.food_item.carbs if meal.food_item else 0) * meal.servings)
        if carb_total < 30:
            return 0
        daily_log = db.get(DailyLog, meal.daily_log_id)
        if not daily_log:
            return 0
        latest = db.scalar(
            select(InsulinScore)
            .where(InsulinScore.daily_log_id == daily_log.id)
            .order_by(InsulinScore.calculated_at.desc())
        )
        if not latest:
            return 0
        db.add(
            InsulinScore(
                daily_log_id=daily_log.id,
                raw_score=float(latest.raw_score) + 10,
                score=float(latest.score) + 10,
            )
        )
        return 1

    def process_apple_steps(self, db: Session, user_id: int, steps_total: int, recorded_at: datetime | None = None) -> dict:
        now = recorded_at or datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        prior_steps = db.scalar(
            select(func.min(ExerciseEntry.step_count))
            .where(
                ExerciseEntry.user_id == user_id,
                ExerciseEntry.activity_type == "apple_step_snapshot",
                ExerciseEntry.performed_at >= one_hour_ago,
                ExerciseEntry.performed_at <= now,
                ExerciseEntry.step_count.is_not(None),
            )
        )
        db.add(
            ExerciseEntry(
                user_id=user_id,
                daily_log_id=None,
                activity_type="apple_step_snapshot",
                exercise_category=ExerciseCategory.WALK,
                movement_type="passive_sync",
                muscle_group="none",
                duration_minutes=1,
                perceived_intensity=1,
                step_count=int(steps_total),
                calories_burned_estimate=0,
                post_meal_walk=False,
                performed_at=now,
            )
        )

        surge_delta = int(steps_total - (prior_steps or steps_total))
        bonus_applied = False
        if surge_delta > 1500:
            bonus_applied = True
            self._mark_post_meal_walk_bonus(db, user_id=user_id, at_time=now, step_delta=surge_delta)

        return {"step_surge": surge_delta, "post_meal_walk_bonus": bonus_applied}

    def _mark_post_meal_walk_bonus(self, db: Session, user_id: int, at_time: datetime, step_delta: int) -> None:
        log = db.scalar(select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date == at_time.date()))
        if not log:
            log = DailyLog(user_id=user_id, log_date=at_time.date())
            db.add(log)
            db.flush()
        db.add(
            ExerciseEntry(
                user_id=user_id,
                daily_log_id=log.id,
                activity_type="apple_step_surge_walk",
                exercise_category=ExerciseCategory.WALK,
                movement_type="step_surge",
                muscle_group="none",
                duration_minutes=20,
                perceived_intensity=4,
                step_count=step_delta,
                calories_burned_estimate=80,
                post_meal_walk=True,
                performed_at=at_time,
            )
        )
        latest_score = db.scalar(
            select(InsulinScore)
            .where(InsulinScore.daily_log_id == log.id)
            .order_by(InsulinScore.calculated_at.desc())
        )
        if latest_score:
            db.add(
                InsulinScore(
                    daily_log_id=log.id,
                    raw_score=max(0.0, float(latest_score.raw_score) - 8),
                    score=max(0.0, float(latest_score.score) - 8),
                )
            )

    def build_panel(self, db: Session, user_id: int) -> dict:
        today = datetime.utcnow().date()
        steps_today = int(
            db.scalar(
                select(func.max(ExerciseEntry.step_count)).where(
                    ExerciseEntry.user_id == user_id,
                    ExerciseEntry.activity_type == "apple_step_snapshot",
                    ExerciseEntry.performed_at >= datetime.combine(today, time.min),
                )
            )
            or 0
        )
        post_meal_walks_today = int(
            db.scalar(
                select(func.count(ExerciseEntry.id)).where(
                    ExerciseEntry.user_id == user_id,
                    ExerciseEntry.performed_at >= datetime.combine(today, time.min),
                    ExerciseEntry.post_meal_walk.is_(True),
                )
            )
            or 0
        )

        streak = self._compute_post_meal_walk_streak(db, user_id=user_id, end_date=today)
        badge = "Insulin Control Streak" if streak >= 5 else None
        recovery_prompt = "Resume today." if streak < 5 else "Keep your streak alive."

        return {
            "post_meal_walk_status": "done" if post_meal_walks_today > 0 else "pending",
            "steps_today": steps_today,
            "walk_streak": streak,
            "recovery_prompt": recovery_prompt,
            "badge": badge,
            "alerts_remaining": max(0, 3 - self._get_today_alert_count(db, user_id, today)),
            "post_meal_walk_bonus": post_meal_walks_today > 0,
        }

    def _compute_post_meal_walk_streak(self, db: Session, user_id: int, end_date: date) -> int:
        streak = 0
        cursor = end_date
        for _ in range(60):
            walks = db.scalar(
                select(func.count(ExerciseEntry.id)).where(
                    ExerciseEntry.user_id == user_id,
                    ExerciseEntry.performed_at >= datetime.combine(cursor, time.min),
                    ExerciseEntry.performed_at <= datetime.combine(cursor, time.max),
                    ExerciseEntry.post_meal_walk.is_(True),
                )
            )
            if not walks:
                break
            streak += 1
            cursor -= timedelta(days=1)
        return streak


movement_engine = MovementEngine()
