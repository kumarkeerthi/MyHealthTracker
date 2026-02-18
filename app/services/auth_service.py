from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    validate_password_policy,
    verify_password,
)
from app.models import AuthLoginAttempt, PasswordResetToken, RefreshToken, User
from app.services.audit_service import audit_service


class AuthService:
    def authenticate(self, db: Session, email: str, password: str, ip_address: str) -> dict:
        normalized_email = email.lower().strip()
        user = db.scalar(select(User).where(User.email == normalized_email))
        now = datetime.utcnow()

        if not user:
            db.add(AuthLoginAttempt(email=normalized_email, ip_address=ip_address, success=False))
            db.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

        if user.locked_until and user.locked_until > now:
            db.add(AuthLoginAttempt(user_id=user.id, email=user.email, ip_address=ip_address, success=False))
            db.commit()
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account temporarily locked")

        if not verify_password(password, user.hashed_password):
            user.failed_attempts += 1
            if user.failed_attempts >= 5:
                user.locked_until = now + timedelta(minutes=15)
            db.add(AuthLoginAttempt(user_id=user.id, email=user.email, ip_address=ip_address, success=False))
            db.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        user.failed_attempts = 0
        user.locked_until = None
        user.last_login = now
        db.add(AuthLoginAttempt(user_id=user.id, email=user.email, ip_address=ip_address, success=True))
        token_bundle = self._issue_token_pair(db, user.id)
        audit_service.log_event(
            db,
            event_type="login_success",
            severity="info",
            user_id=user.id,
            ip_address=ip_address,
            route="/auth/login",
        )
        db.commit()
        return token_bundle

    def register(self, db: Session, email: str, password: str, ip_address: str) -> dict:
        normalized_email = email.lower().strip()
        validate_password_policy(password)
        existing_user = db.scalar(select(User).where(User.email == normalized_email))
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user = User(email=normalized_email, hashed_password=hash_password(password))
        db.add(user)
        db.flush()
        token_bundle = self._issue_token_pair(db, user.id)
        audit_service.log_event(
            db,
            event_type="register_success",
            severity="info",
            user_id=user.id,
            ip_address=ip_address,
            route="/auth/register",
        )
        db.commit()
        return token_bundle

    def _issue_token_pair(self, db: Session, user_id: int) -> dict:
        now = datetime.utcnow()
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        access_token = create_access_token(user_id=user_id, role=user.role)
        refresh_token = create_refresh_token()
        db.add(
            RefreshToken(
                user_id=user_id,
                hashed_token=hash_token(refresh_token),
                expires_at=now + timedelta(days=settings.refresh_token_expiration_days),
                revoked=False,
            )
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in_seconds": settings.jwt_expiration_minutes * 60,
        }

    def get_user_by_id(self, db: Session, user_id: int) -> User:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def rotate_refresh_token(self, db: Session, refresh_token: str) -> dict:
        now = datetime.utcnow()
        token_hash = hash_token(refresh_token)
        stored = db.scalar(select(RefreshToken).where(RefreshToken.hashed_token == token_hash))
        if not stored or stored.revoked or stored.expires_at <= now:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalidated")

        user = db.get(User, stored.user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        stored.revoked = True
        token_bundle = self._issue_token_pair(db, user.id)
        db.commit()
        return token_bundle

    def logout(self, db: Session, refresh_token: str) -> None:
        token_hash = hash_token(refresh_token)
        stored = db.scalar(select(RefreshToken).where(RefreshToken.hashed_token == token_hash))
        if stored and not stored.revoked:
            stored.revoked = True
            db.commit()

    def request_password_reset(self, db: Session, email: str) -> str | None:
        user = db.scalar(select(User).where(User.email == email.lower().strip()))
        if not user:
            return None

        raw_token = create_refresh_token()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                expires_at=datetime.utcnow() + timedelta(minutes=settings.password_reset_token_ttl_minutes),
            )
        )
        db.commit()
        return raw_token

    def confirm_password_reset(self, db: Session, token: str, new_password: str) -> None:
        validate_password_policy(new_password)
        token_hash = hash_token(token)
        stored = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
        now = datetime.utcnow()
        if not stored or stored.used_at is not None or stored.expires_at <= now:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

        user = db.get(User, stored.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.hashed_password = hash_password(new_password)
        stored.used_at = now
        db.commit()


auth_service = AuthService()
