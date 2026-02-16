import os
from celery import Celery
from celery.schedules import crontab

from app.db.session import SessionLocal

broker_url = os.getenv("CELERY_BROKER_URL", "redis://:metabolic@redis:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", broker_url)

celery_app = Celery("metabolic_engine", broker=broker_url, backend=result_backend)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "metabolic-agent-daily-scan": {
            "task": "metabolic_agent.daily_scan",
            "schedule": crontab(hour=4, minute=30),
        },
        "metabolic-agent-weekly-deep-analysis": {
            "task": "metabolic_agent.weekly_analysis",
            "schedule": crontab(day_of_week="mon", hour=5, minute=0),
        },
        "metabolic-agent-monthly-review": {
            "task": "metabolic_agent.monthly_review",
            "schedule": crontab(day_of_month="1", hour=5, minute=30),
        },
    },
)


@celery_app.task(name="health.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="metabolic_agent.daily_scan")
def metabolic_agent_daily_scan() -> dict[str, int]:
    from app.services.metabolic_agent import metabolic_agent_service

    db = SessionLocal()
    try:
        processed = metabolic_agent_service.run_daily_scan_for_all_users(db)
    finally:
        db.close()
    return {"processed_users": processed}


@celery_app.task(name="metabolic_agent.weekly_analysis")
def metabolic_agent_weekly_analysis() -> dict[str, int]:
    from app.services.metabolic_agent import metabolic_agent_service

    db = SessionLocal()
    try:
        processed = metabolic_agent_service.run_weekly_analysis_for_all_users(db)
    finally:
        db.close()
    return {"processed_users": processed}


@celery_app.task(name="metabolic_agent.monthly_review")
def metabolic_agent_monthly_review() -> dict[str, int]:
    from app.services.metabolic_agent import metabolic_agent_service

    db = SessionLocal()
    try:
        processed = metabolic_agent_service.run_monthly_review_for_all_users(db)
    finally:
        db.close()
    return {"processed_users": processed}
