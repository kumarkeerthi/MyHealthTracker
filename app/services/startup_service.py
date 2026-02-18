from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import User


def create_admin_user_if_empty(db: Session) -> None:
    user_count = db.scalar(select(func.count(User.id))) or 0
    if user_count > 0:
        return

    admin_email = settings.admin_email.lower().strip()
    admin_password = settings.admin_password.strip()
    admin_user = User(
        email=admin_email,
        hashed_password=hash_password(admin_password),
        role="admin",
    )
    db.add(admin_user)
    db.commit()
