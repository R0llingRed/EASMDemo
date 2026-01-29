from fastapi import APIRouter

from server.app.api.assets import router as assets_router
from server.app.api.health import router as health_router
from server.app.api.projects import router as projects_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(projects_router)
api_router.include_router(assets_router)
