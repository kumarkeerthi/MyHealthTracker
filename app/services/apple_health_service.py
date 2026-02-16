from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import DailyLog, ExerciseEntry, InsulinScore, User, VitalsEntry
from app.services.exercise_engine import infer_workout_category
from app.services.rule_engine import evaluate_daily_status, get_or_create_metabolic_profile


class AppleHealthService:
    def __init__(self, db: Session):
        self.db = db

    def ingest(self, user: User, payload: dict) -> dict:
        parsed = self._normalize_payload(payload)

        vitals_entry = VitalsEntry(
            user_id=user.id,
            recorded_at=parsed["recorded_at"],
            resting_hr=parsed.get("resting_hr"),
            sleep_hours=parsed.get("sleep_hours"),
            hrv=parsed.get("hrv"),
            vo2_max=parsed.get("vo2_max"),
            hr_zone_1_minutes=parsed.get("heart_rate_zones", {}).get("zone_1", 0),
            hr_zone_2_minutes=parsed.get("heart_rate_zones", {}).get("zone_2", 0),
            hr_zone_3_minutes=parsed.get("heart_rate_zones", {}).get("zone_3", 0),
            hr_zone_4_minutes=parsed.get("heart_rate_zones", {}).get("zone_4", 0),
            hr_zone_5_minutes=parsed.get("heart_rate_zones", {}).get("zone_5", 0),
            steps_total=parsed.get("steps", 0),
        )
        self.db.add(vitals_entry)

        workout_count = 0
        post_meal_detected = 0
        touched_log_ids: set[int] = set()

        for workout in parsed.get("workouts", []):
            performed_at = self._as_datetime(workout.get("performed_at"), parsed["recorded_at"])
            log_date = performed_at.date()
            daily_log = self.db.query(DailyLog).filter_by(user_id=user.id, log_date=log_date).one_or_none()
            if not daily_log:
                daily_log = DailyLog(user_id=user.id, log_date=log_date)
                self.db.add(daily_log)
                self.db.flush()

            activity_type = workout.get("activity_type", workout.get("workout_type", workout.get("movement_type", "apple_workout")))
            movement_type = workout.get("movement_type", activity_type)
            category = infer_workout_category(activity_type, movement_type)

            post_meal_walk = bool(
                workout.get("post_meal_walk", False)
                or (category.value == "WALK" and workout.get("within_60_min_meal", False))
            )
            if post_meal_walk:
                post_meal_detected += 1

            entry = ExerciseEntry(
                user_id=user.id,
                daily_log_id=daily_log.id,
                activity_type=activity_type,
                exercise_category=category,
                movement_type=movement_type,
                muscle_group=workout.get("muscle_group", "full_body"),
                reps=workout.get("reps"),
                sets=workout.get("sets"),
                grip_intensity_score=float(workout.get("grip_intensity_score", 0.0) or 0.0),
                pull_strength_score=float(workout.get("pull_strength_score", 0.0) or 0.0),
                progression_level=int(workout.get("progression_level", 1) or 1),
                dead_hang_duration_seconds=workout.get("dead_hang_duration_seconds"),
                pull_up_count=workout.get("pull_up_count"),
                assisted_pull_up_reps=workout.get("assisted_pull_up_reps"),
                grip_endurance_seconds=workout.get("grip_endurance_seconds"),
                duration_minutes=int(workout.get("duration_minutes", 0) or 0),
                perceived_intensity=workout.get("perceived_intensity", 5),
                step_count=workout.get("step_count"),
                calories_estimate=workout.get("calories_estimate"),
                calories_burned_estimate=workout.get("calories_estimate", 0.0),
                post_meal_walk=post_meal_walk,
                performed_at=performed_at,
            )
            self.db.add(entry)
            touched_log_ids.add(daily_log.id)
            workout_count += 1

        insulin_updates = self._recalculate_daily_scores(user, touched_log_ids)
        self.db.commit()

        return {
            "vitals_entry_id": vitals_entry.id,
            "workouts_imported": workout_count,
            "post_meal_workouts_detected": post_meal_detected,
            "heart_rate_zones_synced": bool(parsed.get("heart_rate_zones")),
            "hrv_synced": parsed.get("hrv") is not None,
            "vo2_max_synced": parsed.get("vo2_max") is not None,
            "insulin_scores_updated": insulin_updates,
        }

    def _recalculate_daily_scores(self, user: User, touched_log_ids: set[int]) -> int:
        if not touched_log_ids:
            return 0

        profile = get_or_create_metabolic_profile(self.db, user)
        logs = self.db.scalars(
            select(DailyLog)
            .options(selectinload(DailyLog.meal_entries))
            .where(DailyLog.id.in_(touched_log_ids))
        ).all()

        updates = 0
        for daily_log in logs:
            if not daily_log.meal_entries:
                continue
            status = evaluate_daily_status(self.db, daily_log, profile)
            self.db.add(
                InsulinScore(
                    daily_log_id=daily_log.id,
                    score=status["insulin_load_score"],
                    raw_score=status["insulin_load_raw_score"],
                )
            )
            updates += 1
        return updates

    def _normalize_payload(self, payload: dict) -> dict:
        source_payload = payload.get("health_export") or payload.get("relay") or payload

        steps = source_payload.get("steps", 0)
        resting_hr = source_payload.get("resting_heart_rate") or source_payload.get("resting_hr")
        sleep_hours = source_payload.get("sleep_hours") or source_payload.get("sleep", {}).get("hours")
        workouts = source_payload.get("workouts", [])
        hrv = source_payload.get("hrv")
        vo2_max = source_payload.get("vo2_max")
        heart_rate_zones = source_payload.get("heart_rate_zones", {})
        recorded_at_raw = source_payload.get("recorded_at")
        recorded_at = self._as_datetime(recorded_at_raw, datetime.now(timezone.utc).replace(tzinfo=None))

        return {
            "steps": int(steps or 0),
            "resting_hr": resting_hr,
            "sleep_hours": sleep_hours,
            "workouts": workouts,
            "hrv": hrv,
            "vo2_max": vo2_max,
            "heart_rate_zones": heart_rate_zones,
            "recorded_at": recorded_at,
        }

    @staticmethod
    def _as_datetime(value: str | None, fallback: datetime) -> datetime:
        if not value:
            return fallback
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
