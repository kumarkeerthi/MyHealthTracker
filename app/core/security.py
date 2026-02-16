import hashlib
import html
import json
import re
import secrets
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

SCRIPT_PATTERN = re.compile(r"<\s*script", flags=re.IGNORECASE)
JS_URI_PATTERN = re.compile(r"javascript:\s*", flags=re.IGNORECASE)


@dataclass
class RateLimitRule:
    limit: int
    window_seconds: int


class SlidingWindowLimiter:
    def __init__(self):
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def is_allowed(self, key: str, rule: RateLimitRule) -> bool:
        now = time.time()
        window_start = now - rule.window_seconds
        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            if len(bucket) >= rule.limit:
                return False
            bucket.append(now)
            return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, default_rule: RateLimitRule):
        super().__init__(app)
        self.default_rule = default_rule
        self.limiter = SlidingWindowLimiter()

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"
        if not self.limiter.is_allowed(key, self.default_rule):
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Please retry later."})
        return await call_next(request)


class HTTPSRedirectEnforcementMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.require_https:
            return await call_next(request)

        if request.url.path in {"/health", "/metrics"}:
            return await call_next(request)

        proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        if proto != "https":
            return JSONResponse(status_code=400, content={"detail": "HTTPS is required"})
        return await call_next(request)


class AuthRequiredMiddleware(BaseHTTPMiddleware):
    PUBLIC_PATHS = {"/health", "/metrics", "/auth/login", "/auth/refresh", "/auth/password-reset/request", "/auth/password-reset/confirm"}

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Bearer token required"})

        token = authorization.replace("Bearer ", "", 1).strip()
        try:
            claims = decode_token(token)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

        if claims.get("type") != "access":
            return JSONResponse(status_code=401, content={"detail": "Access token required"})

        request.state.token_claims = claims
        return await call_next(request)


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        async def receive() -> dict[str, Any]:
            return {"type": "http.request", "body": body, "more_body": False}

        body = await request.body()
        content_type = request.headers.get("content-type", "")

        if body and "application/json" in content_type:
            try:
                payload = json.loads(body)
                sanitized = _sanitize_payload(payload)
                body = json.dumps(sanitized).encode("utf-8")
            except json.JSONDecodeError:
                pass

        request._receive = receive
        return await call_next(request)


class LLMUsageLimiter:
    def __init__(self):
        self._events: dict[int, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check_and_increment(self, user_id: int, limit_per_hour: int) -> bool:
        now = time.time()
        hour_ago = now - 3600
        with self._lock:
            bucket = self._events[user_id]
            while bucket and bucket[0] < hour_ago:
                bucket.popleft()
            if len(bucket) >= limit_per_hour:
                return False
            bucket.append(now)
            return True


llm_usage_limiter = LLMUsageLimiter()


def sanitize_text(value: str) -> str:
    cleaned = SCRIPT_PATTERN.sub("", value)
    cleaned = JS_URI_PATTERN.sub("", cleaned)
    return html.escape(cleaned.strip())


def _sanitize_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {k: _sanitize_payload(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [_sanitize_payload(item) for item in payload]
    if isinstance(payload, str):
        return sanitize_text(payload)
    return payload


def hash_password(plain_password: str) -> str:
    rounds = max(4, settings.auth_bcrypt_rounds)
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def _build_claims(*, user_id: int, role: str, token_type: str, expires_delta: timedelta) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "sub": str(user_id),
        "role": role,
        "type": token_type,
        "jti": secrets.token_urlsafe(16),
        "exp": now + expires_delta,
        "iat": now,
    }


def create_access_token(user_id: int, role: str) -> str:
    claims = _build_claims(
        user_id=user_id,
        role=role,
        token_type="access",
        expires_delta=timedelta(minutes=settings.jwt_expiration_minutes),
    )
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int, role: str) -> str:
    claims = _build_claims(
        user_id=user_id,
        role=role,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expiration_days),
    )
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc


def get_current_token_claims(authorization: str = Header(default="")) -> dict[str, Any]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    token = authorization.replace("Bearer ", "", 1).strip()
    claims = decode_token(token)
    if claims.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token required")
    return claims


def require_admin(claims: dict[str, Any] = Depends(get_current_token_claims)) -> dict[str, Any]:
    if claims.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return claims
