import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import PushSubscription

try:
    from pywebpush import WebPushException, webpush
except Exception:  # pragma: no cover - dependency may be unavailable in some envs
    WebPushException = Exception
    webpush = None


class PushService:
    def upsert_subscription(self, db: Session, user_id: int, payload: dict) -> PushSubscription:
        endpoint = payload.get("endpoint")
        keys = payload.get("keys") or {}
        record = db.scalar(select(PushSubscription).where(PushSubscription.endpoint == endpoint))

        expiration = payload.get("expirationTime")
        expiration_time = None
        if expiration:
            try:
                expiration_time = datetime.fromisoformat(str(expiration).replace("Z", "+00:00"))
            except ValueError:
                expiration_time = None

        if record:
            record.user_id = user_id
            record.p256dh = keys.get("p256dh", "")
            record.auth = keys.get("auth", "")
            record.expiration_time = expiration_time
            record.user_agent = payload.get("user_agent")
            return record

        record = PushSubscription(
            user_id=user_id,
            endpoint=endpoint,
            p256dh=keys.get("p256dh", ""),
            auth=keys.get("auth", ""),
            expiration_time=expiration_time,
            user_agent=payload.get("user_agent"),
        )
        db.add(record)
        db.flush()
        return record

    def send_to_user(self, db: Session, user_id: int, title: str, body: str, payload: dict | None = None) -> dict:
        payload = payload or {}
        rows = db.scalars(select(PushSubscription).where(PushSubscription.user_id == user_id)).all()
        if not rows:
            return {"status": "skipped", "reason": "no_subscription", "sent": 0}

        if not webpush or not settings.vapid_private_key or not settings.vapid_public_key:
            return {"status": "skipped", "reason": "webpush_not_configured", "sent": 0}

        sent = 0
        failed = 0
        for sub in rows:
            subscription_info = {
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
            }
            try:
                webpush(
                    subscription_info=subscription_info,
                    data=json.dumps({"title": title, "body": body, "payload": payload}),
                    vapid_private_key=settings.vapid_private_key,
                    vapid_claims={"sub": settings.vapid_subject},
                )
                sent += 1
            except WebPushException:
                failed += 1

        return {"status": "sent" if sent else "skipped", "sent": sent, "failed": failed}


push_service = PushService()
