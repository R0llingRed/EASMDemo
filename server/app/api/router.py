from fastapi import APIRouter

from server.app.api.assets import router as assets_router
from server.app.api.health import router as health_router
from server.app.api.ips import router as ips_router
from server.app.api.ports import router as ports_router
from server.app.api.projects import router as projects_router
from server.app.api.scans import router as scans_router
from server.app.api.subdomains import router as subdomains_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(projects_router)
api_router.include_router(assets_router)
api_router.include_router(scans_router)
api_router.include_router(subdomains_router)
api_router.include_router(ips_router)
api_router.include_router(ports_router)
