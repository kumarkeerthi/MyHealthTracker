from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyLog, NotificationSettings, User


class NotificationService:
    def get_or_create_settings(self, db: Session, user_id: int) -> NotificationSettings:
        settings = db.scalar(select(NotificationSettings).where(NotificationSettings.user_id == user_id))
        if settings:
            return settings

        settings = NotificationSettings(user_id=user_id)
        db.add(settings)
        db.flush()
        return settings

    def _can_send(self, settings: NotificationSettings, channel: str) -> bool:
        if settings.silent_mode:
            return False
        if channel == "whatsapp":
            return settings.whatsapp_enabled
        if channel == "push":
            return settings.push_enabled
        if channel == "email":
            return settings.email_enabled
        return False

    def send_message(self, db: Session, user_id: int, channel: str, title: str, body: str, metadata: dict | None = None) -> dict:
        user = db.get(User, user_id)
        if not user:
            return {
                "status": "skipped",
                "reason": "user_not_found",
                "channel": channel,
                "title": title,
                "body": body,
            }

        settings = self.get_or_create_settings(db, user_id)
        if not self._can_send(settings, channel):
            return {
                "status": "skipped",
                "reason": "channel_disabled_or_silent_mode",
                "channel": channel,
                "title": title,
                "body": body,
            }

        return {
            "status": "sent",
            "channel": channel,
            "title": title,
            "body": body,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

    def evaluate_daily_alerts(self, db: Session, user_id: int, daily_log: DailyLog, insulin_score: float) -> list[dict]:
        alerts: list[dict] = []

        if insulin_score > 70:
            alerts.append(
                self.send_message(
                    db,
                    user_id,
                    channel="push",
                    title="Metabolic Alert",
                    body="High carb load detected. 20 min walk suggested.",
                    metadata={"insulin_score": insulin_score},
                )
            )

        if daily_log.total_protein < 80:
            alerts.append(
                self.send_message(
                    db,
                    user_id,
                    channel="push",
                    title="Protein Alert",
                    body="HDL support compromised.",
                    metadata={"protein": daily_log.total_protein},
                )
            )

        return alerts


notification_service = NotificationService()
