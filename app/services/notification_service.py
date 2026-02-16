from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyLog, NotificationSettings, User
from app.services.push_service import push_service


class NotificationService:
    def get_or_create_settings(self, db: Session, user_id: int) -> NotificationSettings:
        settings = db.scalar(select(NotificationSettings).where(NotificationSettings.user_id == user_id))
        if settings:
            return settings

        settings = NotificationSettings(user_id=user_id)
        db.add(settings)
        db.flush()
        return settings

    def _within_quiet_hours(self, settings: NotificationSettings) -> bool:
        if not settings.quiet_hours_start or not settings.quiet_hours_end:
            return False
        now = datetime.utcnow().time()
        start = datetime.strptime(settings.quiet_hours_start, "%H:%M").time()
        end = datetime.strptime(settings.quiet_hours_end, "%H:%M").time()
        if start <= end:
            return start <= now <= end
        return now >= start or now <= end

    def _can_send(self, settings: NotificationSettings, channel: str) -> bool:
        if settings.silent_mode or self._within_quiet_hours(settings):
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

        if channel == "push":
            push_result = push_service.send_to_user(db, user_id, title=title, body=body, payload=metadata or {})
            if push_result.get("status") == "skipped":
                return {
                    "status": "skipped",
                    "reason": push_result.get("reason"),
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
        settings = self.get_or_create_settings(db, user_id)

        if insulin_score > 70 and settings.insulin_alerts_enabled:
            alerts.append(
                self.send_message(
                    db,
                    user_id,
                    channel="push",
                    title="Metabolic Alert",
                    body="High insulin load – 20 min walk recommended.",
                    metadata={"insulin_score": insulin_score},
                )
            )

        if daily_log.total_protein < 80 and settings.protein_reminders_enabled:
            alerts.append(
                self.send_message(
                    db,
                    user_id,
                    channel="push",
                    title="Protein Alert",
                    body="Protein first.",
                    metadata={"protein": daily_log.total_protein},
                )
            )

        return alerts


notification_service = NotificationService()
