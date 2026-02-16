import html
import json
import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any

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


def create_access_token(user_id: int, is_admin: bool) -> str:
    expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)
    expires_at = datetime.now(timezone.utc) + expires_delta
    claims = {
        "sub": str(user_id),
        "is_admin": is_admin,
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc


def get_current_token_claims(authorization: str = Header(default="")) -> dict[str, Any]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    token = authorization.replace("Bearer ", "", 1).strip()
    return decode_token(token)


def require_admin(claims: dict[str, Any] = Depends(get_current_token_claims)) -> dict[str, Any]:
    if not claims.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return claims
