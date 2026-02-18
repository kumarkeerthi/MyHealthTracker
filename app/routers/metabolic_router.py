from fastapi import APIRouter

from app.api.routes import router as core_router
from app.routers.copilot_router import copilot_router

router = APIRouter()
router.include_router(core_router)
router.include_router(copilot_router)

__all__ = ["router"]
