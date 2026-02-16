from datetime import datetime

from sqlalchemy.orm import Session

from app.models import DailyLog, ExerciseCategory, ExerciseEntry, User, VitalsEntry


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
            steps_total=parsed.get("steps", 0),
        )
        self.db.add(vitals_entry)

        workout_count = 0
        for workout in parsed.get("workouts", []):
            log_date = parsed["recorded_at"].date()
            daily_log = self.db.query(DailyLog).filter_by(user_id=user.id, log_date=log_date).one_or_none()
            if not daily_log:
                daily_log = DailyLog(user_id=user.id, log_date=log_date)
                self.db.add(daily_log)
                self.db.flush()

            entry = ExerciseEntry(
                user_id=user.id,
                daily_log_id=daily_log.id,
                activity_type=workout.get("activity_type", workout.get("movement_type", "apple_workout")),
                exercise_category=ExerciseCategory(workout.get("exercise_category", "STRENGTH")),
                movement_type=workout.get("movement_type", "apple_workout"),
                duration_minutes=workout.get("duration_minutes", 0),
                perceived_intensity=workout.get("perceived_intensity", 5),
                step_count=workout.get("step_count"),
                calories_estimate=workout.get("calories_estimate"),
                calories_burned_estimate=workout.get("calories_estimate", 0.0),
                post_meal_walk=workout.get("post_meal_walk", False),
                performed_at=parsed["recorded_at"],
            )
            self.db.add(entry)
            workout_count += 1

        self.db.commit()
        return {"vitals_entry_id": vitals_entry.id, "workouts_imported": workout_count}

    def _normalize_payload(self, payload: dict) -> dict:
        source_payload = payload.get("health_export") or payload.get("relay") or payload

        steps = source_payload.get("steps", 0)
        resting_hr = source_payload.get("resting_heart_rate") or source_payload.get("resting_hr")
        sleep_hours = source_payload.get("sleep_hours")
        workouts = source_payload.get("workouts", [])
        recorded_at_raw = source_payload.get("recorded_at")
        recorded_at = datetime.fromisoformat(recorded_at_raw) if recorded_at_raw else datetime.utcnow()

        return {
            "steps": int(steps or 0),
            "resting_hr": resting_hr,
            "sleep_hours": sleep_hours,
            "workouts": workouts,
            "recorded_at": recorded_at,
        }
