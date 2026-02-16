import json

from sqlalchemy.orm import Session

from app.models import SecurityAuditLog


class AuditService:
    def log_event(
        self,
        db: Session,
        *,
        event_type: str,
        severity: str = "info",
        user_id: int | None = None,
        ip_address: str | None = None,
        route: str | None = None,
        details: dict | None = None,
    ) -> None:
        db.add(
            SecurityAuditLog(
                user_id=user_id,
                event_type=event_type,
                severity=severity,
                ip_address=ip_address,
                route=route,
                details=json.dumps(details or {}),
            )
        )


audit_service = AuditService()
