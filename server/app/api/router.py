from fastapi import APIRouter, Depends

from server.app.api.api_endpoints import router as api_endpoints_router
from server.app.api.api_risks import router as api_risks_router
from server.app.api.alerts import router as alerts_router
from server.app.api.assets import router as assets_router
from server.app.api.dag_executions import router as dag_executions_router
from server.app.api.dag_templates import router as dag_templates_router
from server.app.api.event_triggers import events_router, router as event_triggers_router
from server.app.api.health import router as health_router
from server.app.api.ips import router as ips_router
from server.app.api.js_assets import router as js_assets_router
from server.app.api.notifications import router as notifications_router
from server.app.api.policies import router as policies_router
from server.app.api.ports import router as ports_router
from server.app.api.projects import router as projects_router
from server.app.api.risk import router as risk_router
from server.app.api.scans import router as scans_router
from server.app.api.subdomains import router as subdomains_router
from server.app.api.vulnerabilities import router as vulnerabilities_router
from server.app.api.web_assets import router as web_assets_router
from server.app.api.deps import require_api_key

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(projects_router, dependencies=[Depends(require_api_key)])
api_router.include_router(assets_router, dependencies=[Depends(require_api_key)])
api_router.include_router(js_assets_router, dependencies=[Depends(require_api_key)])
api_router.include_router(api_endpoints_router, dependencies=[Depends(require_api_key)])
api_router.include_router(api_risks_router, dependencies=[Depends(require_api_key)])
api_router.include_router(scans_router, dependencies=[Depends(require_api_key)])
api_router.include_router(subdomains_router, dependencies=[Depends(require_api_key)])
api_router.include_router(ips_router, dependencies=[Depends(require_api_key)])
api_router.include_router(ports_router, dependencies=[Depends(require_api_key)])
api_router.include_router(web_assets_router, dependencies=[Depends(require_api_key)])
api_router.include_router(vulnerabilities_router, dependencies=[Depends(require_api_key)])
api_router.include_router(policies_router, dependencies=[Depends(require_api_key)])
api_router.include_router(dag_templates_router, dependencies=[Depends(require_api_key)])
api_router.include_router(dag_executions_router, dependencies=[Depends(require_api_key)])
api_router.include_router(event_triggers_router, dependencies=[Depends(require_api_key)])
api_router.include_router(events_router, dependencies=[Depends(require_api_key)])
api_router.include_router(risk_router, dependencies=[Depends(require_api_key)])
api_router.include_router(alerts_router, dependencies=[Depends(require_api_key)])
api_router.include_router(notifications_router, dependencies=[Depends(require_api_key)])
