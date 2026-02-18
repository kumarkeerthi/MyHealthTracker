import logging
from sqlalchemy import text
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import router
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.monitoring import MetricsMiddleware, metrics_response
from app.core.security import (
    AuthRequiredMiddleware,
    HTTPSRedirectEnforcementMiddleware,
    CSRFMiddleware,
    InputSanitizationMiddleware,
    RateLimitMiddleware,
    RateLimitRule,
    SecurityHeadersMiddleware,
)
from app.data.seed_data import seed_initial_data
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.coaching_scheduler import coaching_scheduler
from app.services.metabolic_advisor_scheduler import metabolic_advisor_scheduler
from app.services.startup_service import create_admin_user_if_empty

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
allowed_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-CSRF-Token"],
)
app.add_middleware(HTTPSRedirectEnforcementMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(InputSanitizationMiddleware)
app.add_middleware(AuthRequiredMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    default_rule=RateLimitRule(limit=settings.rate_limit_requests, window_seconds=settings.rate_limit_window_seconds),
    route_rules={
        "/llm": RateLimitRule(limit=max(1, settings.llm_requests_per_hour // 2), window_seconds=60),
    },
)
app.add_middleware(MetricsMiddleware)
app.include_router(router)


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        create_admin_user_if_empty(db)
        seed_initial_data(db)
    finally:
        db.close()
    coaching_scheduler.start()
    metabolic_advisor_scheduler.start()
    logger.info("Application startup complete")


@app.on_event("shutdown")
def shutdown_event():
    coaching_scheduler.shutdown()
    metabolic_advisor_scheduler.shutdown()
    logger.info("Application shutdown complete")


@app.get("/health")
def health_check():
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    status = "ok" if db_ok else "degraded"
    return {"status": status, "service": settings.app_name, "database": "up" if db_ok else "down"}


@app.get("/metrics")
def metrics():
    return metrics_response()
