from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import User
from app.services.metabolic_advisor_service import metabolic_advisor_service


class MetabolicAdvisorScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self.started = False

    def _run_weekly(self):
        db = SessionLocal()
        try:
            users = db.scalars(select(User)).all()
            for user in users:
                metabolic_advisor_service.run_weekly_recommendations(db, user.id)
        finally:
            db.close()

    def start(self):
        if self.started:
            return

        # Monday 05:00 UTC
        self.scheduler.add_job(
            self._run_weekly,
            "cron",
            day_of_week="mon",
            hour=5,
            minute=0,
            id="weekly_metabolic_advisor",
            replace_existing=True,
        )
        self.scheduler.start()
        self.started = True

    def shutdown(self):
        if self.started:
            self.scheduler.shutdown(wait=False)
            self.started = False


metabolic_advisor_scheduler = MetabolicAdvisorScheduler()
