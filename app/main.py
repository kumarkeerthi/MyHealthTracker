from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings
from app.data.seed_data import seed_initial_data
from app.db.base import Base
from app.db.session import SessionLocal, engine

app = FastAPI(title=settings.app_name)
app.include_router(router)


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.app_name}
