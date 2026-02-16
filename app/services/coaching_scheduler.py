from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.services.notification_service import notification_service


class CoachingScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self.started = False

    def _send_coaching_message(self, user_id: int, channel: str, title: str, body: str):
        db = SessionLocal()
        try:
            notification_service.send_message(
                db,
                user_id=user_id,
                channel=channel,
                title=title,
                body=body,
                metadata={"source": "daily_scheduler"},
            )
            db.commit()
        finally:
            db.close()

    def start(self):
        if self.started:
            return

        # 8 AM UTC
        self.scheduler.add_job(
            self._send_coaching_message,
            "cron",
            hour=8,
            minute=0,
            kwargs={"user_id": 1, "channel": "whatsapp", "title": "Morning Coaching", "body": "Protein first."},
            id="daily_morning_coaching",
            replace_existing=True,
        )
        # 1 PM UTC
        self.scheduler.add_job(
            self._send_coaching_message,
            "cron",
            hour=13,
            minute=0,
            kwargs={
                "user_id": 1,
                "channel": "whatsapp",
                "title": "Lunch Coaching",
                "body": "Eat vegetables before chapati.",
            },
            id="daily_lunch_coaching",
            replace_existing=True,
        )
        # 6 PM UTC
        self.scheduler.add_job(
            self._send_coaching_message,
            "cron",
            hour=18,
            minute=0,
            kwargs={
                "user_id": 1,
                "channel": "whatsapp",
                "title": "Evening Coaching",
                "body": "If hungry, drink water. Fasting window active.",
            },
            id="daily_evening_coaching",
            replace_existing=True,
        )

        self.scheduler.start()
        self.started = True

    def shutdown(self):
        if self.started:
            self.scheduler.shutdown(wait=False)
            self.started = False


coaching_scheduler = CoachingScheduler()
