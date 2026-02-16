from datetime import date, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import DailyLog, ExerciseEntry, InsulinScore, User
from app.services.notification_service import notification_service


class CoachingScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self.started = False

    def _send_coaching_message(self, user_id: int, title: str, body: str, category_toggle: str | None = None):
        db = SessionLocal()
        try:
            settings = notification_service.get_or_create_settings(db, user_id)
            if category_toggle and not getattr(settings, category_toggle, True):
                return
            notification_service.send_message(
                db,
                user_id=user_id,
                channel="push",
                title=title,
                body=body,
                metadata={"source": "daily_scheduler"},
            )
            db.commit()
        finally:
            db.close()

    def _send_all_users(self, title: str, body: str, category_toggle: str | None = None):
        db = SessionLocal()
        try:
            user_ids = db.scalars(select(User.id)).all()
        finally:
            db.close()
        for user_id in user_ids:
            self._send_coaching_message(user_id=user_id, title=title, body=body, category_toggle=category_toggle)

    def _check_dynamic_alerts(self):
        db = SessionLocal()
        try:
            users = db.scalars(select(User)).all()
            today = date.today()
            for user in users:
                latest_daily_log = db.scalar(
                    select(DailyLog)
                    .where(DailyLog.user_id == user.id, DailyLog.log_date == today)
                    .order_by(DailyLog.id.desc())
                    .limit(1)
                )
                if latest_daily_log:
                    insulin_score = db.scalar(
                        select(InsulinScore.score)
                        .where(InsulinScore.daily_log_id == latest_daily_log.id)
                        .order_by(InsulinScore.calculated_at.desc())
                        .limit(1)
                    )
                    if insulin_score and insulin_score > 70:
                        self._send_coaching_message(
                            user_id=user.id,
                            title="Metabolic Alert",
                            body="High insulin load – 20 min walk recommended.",
                            category_toggle="insulin_alerts_enabled",
                        )

                    if datetime.utcnow().hour >= 16 and latest_daily_log.water_ml < 1500:
                        self._send_coaching_message(
                            user_id=user.id,
                            title="Hydration Check",
                            body="Hydration check – have you had water?",
                            category_toggle="hydration_alerts_enabled",
                        )

                since = datetime.utcnow() - timedelta(days=3)
                recent_strength = db.scalar(
                    select(ExerciseEntry.id)
                    .where(ExerciseEntry.user_id == user.id, ExerciseEntry.performed_at >= since)
                    .limit(1)
                )
                if not recent_strength:
                    self._send_coaching_message(
                        user_id=user.id,
                        title="Strength Reminder",
                        body="Grip strength needs stimulus.",
                        category_toggle="strength_reminders_enabled",
                    )
        finally:
            db.close()

    def start(self):
        if self.started:
            return

        self.scheduler.add_job(
            self._send_all_users,
            "cron",
            hour=8,
            minute=0,
            kwargs={"title": "Morning Coaching", "body": "Protein first.", "category_toggle": "protein_reminders_enabled"},
            id="daily_morning_coaching",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._send_all_users,
            "cron",
            hour=12,
            minute=30,
            kwargs={"title": "Lunch Coaching", "body": "Eat vegetables before chapati.", "category_toggle": "protein_reminders_enabled"},
            id="daily_lunch_coaching",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._send_all_users,
            "cron",
            hour=14,
            minute=15,
            kwargs={"title": "Fasting Alert", "body": "Fasting window active.", "category_toggle": "fasting_alerts_enabled"},
            id="daily_fasting_alert",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._send_all_users,
            "cron",
            hour=16,
            minute=0,
            kwargs={"title": "Hydration Check", "body": "Hydration check – have you had water?", "category_toggle": "hydration_alerts_enabled"},
            id="daily_hydration_prompt",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._check_dynamic_alerts,
            "interval",
            minutes=30,
            id="dynamic_metabolic_alerts",
            replace_existing=True,
        )

        self.scheduler.start()
        self.started = True

    def shutdown(self):
        if self.started:
            self.scheduler.shutdown(wait=False)
            self.started = False


coaching_scheduler = CoachingScheduler()
