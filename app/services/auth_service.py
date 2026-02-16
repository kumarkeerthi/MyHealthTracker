from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import AuthLoginAttempt, AuthRefreshToken, PasswordResetToken, User


class AuthService:
    def authenticate(self, db: Session, email: str, password: str, ip_address: str) -> dict:
        user = db.scalar(select(User).where(User.email == email.lower().strip()))
        now = datetime.utcnow()

        if not user:
            db.add(AuthLoginAttempt(email=email.lower().strip(), ip_address=ip_address, success=False))
            db.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if user.locked_until and user.locked_until > now:
            db.add(AuthLoginAttempt(user_id=user.id, email=user.email, ip_address=ip_address, success=False))
            db.commit()
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account temporarily locked")

        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = now + timedelta(minutes=30)
            db.add(AuthLoginAttempt(user_id=user.id, email=user.email, ip_address=ip_address, success=False))
            db.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        user.failed_login_attempts = 0
        user.locked_until = None
        db.add(AuthLoginAttempt(user_id=user.id, email=user.email, ip_address=ip_address, success=True))

        access_token = create_access_token(user_id=user.id, role=user.role)
        refresh_token = create_refresh_token(user_id=user.id, role=user.role)
        db.add(
            AuthRefreshToken(
                user_id=user.id,
                token_hash=hash_token(refresh_token),
                expires_at=now + timedelta(days=settings.refresh_token_expiration_days),
                ip_address=ip_address,
            )
        )
        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in_seconds": settings.jwt_expiration_minutes * 60,
        }

    def rotate_refresh_token(self, db: Session, refresh_token: str, ip_address: str) -> dict:
        claims = decode_token(refresh_token)
        if claims.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required")

        token_hash = hash_token(refresh_token)
        stored = db.scalar(select(AuthRefreshToken).where(AuthRefreshToken.token_hash == token_hash))
        now = datetime.utcnow()
        if not stored or stored.revoked_at is not None or stored.expires_at <= now:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalidated")

        user = db.get(User, int(claims["sub"]))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        new_access = create_access_token(user_id=user.id, role=user.role)
        new_refresh = create_refresh_token(user_id=user.id, role=user.role)
        new_hash = hash_token(new_refresh)

        stored.revoked_at = now
        stored.replaced_by_token_hash = new_hash
        db.add(
            AuthRefreshToken(
                user_id=user.id,
                token_hash=new_hash,
                expires_at=now + timedelta(days=settings.refresh_token_expiration_days),
                ip_address=ip_address,
            )
        )
        db.commit()

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "expires_in_seconds": settings.jwt_expiration_minutes * 60,
        }

    def logout(self, db: Session, refresh_token: str) -> None:
        token_hash = hash_token(refresh_token)
        stored = db.scalar(select(AuthRefreshToken).where(AuthRefreshToken.token_hash == token_hash))
        if stored and stored.revoked_at is None:
            stored.revoked_at = datetime.utcnow()
            db.commit()

    def request_password_reset(self, db: Session, email: str) -> str | None:
        user = db.scalar(select(User).where(User.email == email.lower().strip()))
        if not user:
            return None

        raw = create_refresh_token(user_id=user.id, role=user.role)
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token(raw),
                expires_at=datetime.utcnow() + timedelta(minutes=settings.password_reset_token_ttl_minutes),
            )
        )
        db.commit()
        return raw

    def confirm_password_reset(self, db: Session, token: str, new_password: str) -> None:
        token_hash = hash_token(token)
        now = datetime.utcnow()
        reset = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
        if not reset or reset.used_at is not None or reset.expires_at <= now:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

        user = db.get(User, reset.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.hashed_password = hash_password(new_password)
        reset.used_at = now
        db.commit()


auth_service = AuthService()
