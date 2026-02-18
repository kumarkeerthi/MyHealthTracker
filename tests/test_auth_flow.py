from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import router
from app.core.config import settings
from app.core.security import CSRFMiddleware, InputSanitizationMiddleware, RateLimitMiddleware, RateLimitRule, SecurityHeadersMiddleware
from app.db.base import Base
from app.db.session import get_db


def build_test_client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    allow_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(InputSanitizationMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        default_rule=RateLimitRule(limit=settings.rate_limit_requests, window_seconds=settings.rate_limit_window_seconds),
    )

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(router)
    return TestClient(app)


def test_register_login_refresh_http():
    prior_environment = settings.environment
    settings.environment = "development"
    try:
        client = build_test_client()

        register_response = client.post("/auth/register", json={"email": "tester@example.com", "password": "Password123"})
        assert register_response.status_code == 200
        set_cookie = register_response.headers.get("set-cookie", "").lower()
        assert "refresh_token=" in set_cookie
        assert "secure" not in set_cookie

        refresh_response = client.post("/auth/refresh")
        assert refresh_response.status_code == 200
        payload = refresh_response.json()
        assert payload.get("access_token")
    finally:
        settings.environment = prior_environment


def test_refresh_without_cookie():
    client = build_test_client()
    response = client.post("/auth/refresh")
    assert response.status_code == 403


def test_csrf_does_not_block_auth():
    client = build_test_client()
    response = client.options("/auth/login")
    assert response.status_code == 200
