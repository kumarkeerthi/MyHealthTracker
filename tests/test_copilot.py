from collections.abc import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.security import CSRFMiddleware, InputSanitizationMiddleware, RateLimitMiddleware, RateLimitRule, SecurityHeadersMiddleware
from app.db.base import Base
from app.db.session import get_db
from app.models import AIActionLog, DailyLog
from app.routers import router
from app.services.metabolic_copilot_service import metabolic_copilot_service


def build_test_client() -> tuple[TestClient, sessionmaker]:
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
    return TestClient(app), SessionLocal


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/auth/register", json={"email": "copilot@example.com", "password": "Password123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def with_fake_llm(fn: Callable[[], None]) -> None:
    original = metabolic_copilot_service._call_structured_llm

    async def fake_llm(**_kwargs):
        return {
            "assistant_message": "Logged your meal.",
            "action": {
                "action": "log_meal",
                "items": ["dal makhani", "chapati"],
                "estimated_macros": {"protein": 20, "carbs": 45, "fats": 14, "hidden_oil": 3},
                "confidence": 0.91,
            },
        }

    metabolic_copilot_service._call_structured_llm = fake_llm
    try:
        fn()
    finally:
        metabolic_copilot_service._call_structured_llm = original


def test_conversation_creation_and_persistence():
    client, _session_local = build_test_client()
    headers = auth_headers(client)

    def run_case():
        response = client.post("/copilot/message", json={"message": "Can I eat paneer tonight?"}, headers=headers)
        assert response.status_code == 200
        payload = response.json()
        assert payload["conversation_id"] > 0

        conversations = client.get("/copilot/conversations", headers=headers)
        assert conversations.status_code == 200
        assert len(conversations.json()) == 1

    with_fake_llm(run_case)


def test_meal_logging_via_ai_creates_daily_log_and_action_record():
    client, session_local = build_test_client()
    headers = auth_headers(client)

    def run_case():
        response = client.post("/copilot/message", json={"message": "I had dal makhani and 2 chapati"}, headers=headers)
        assert response.status_code == 200

        with session_local() as db:
            daily = db.scalar(select(DailyLog))
            action = db.scalar(select(AIActionLog))
            assert daily is not None
            assert daily.total_carbs > 0
            assert action is not None
            assert action.action_type == "meal_logged"

    with_fake_llm(run_case)


def test_action_json_parsing_returns_actions_executed():
    client, _session_local = build_test_client()
    headers = auth_headers(client)

    def run_case():
        response = client.post("/copilot/message", json={"message": "I had dal and chapati"}, headers=headers)
        assert response.status_code == 200
        payload = response.json()
        assert payload["actions_executed"]
        assert payload["actions_executed"][0]["action_type"] == "meal_logged"

    with_fake_llm(run_case)


def test_unauthorized_access_rejected():
    client, _session_local = build_test_client()
    response = client.get("/copilot/conversations")
    assert response.status_code == 401


def test_token_limit_enforced_for_daily_usage():
    client, _session_local = build_test_client()
    headers = auth_headers(client)
    prior_limit = settings.llm_requests_per_day
    settings.llm_requests_per_day = 0

    try:
        response = client.post("/copilot/message", json={"message": "Hello"}, headers=headers)
        assert response.status_code == 429
    finally:
        settings.llm_requests_per_day = prior_limit
