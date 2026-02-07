from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud import scan_policy as crud_scan_policy
from server.app.crud import scan_task as crud_scan_task
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.common import Page
from server.app.schemas.scan_task import ScanTaskCreate, ScanTaskOut
from worker.app.tasks import fingerprint as fingerprint_tasks
from worker.app.tasks import http_probe as http_probe_tasks
from worker.app.tasks import js_api_discovery as js_api_discovery_tasks
from worker.app.tasks import nuclei_scan as nuclei_tasks
from worker.app.tasks import scan as scan_tasks
from worker.app.tasks import screenshot as screenshot_tasks
from worker.app.tasks import xray_scan as xray_tasks

router = APIRouter(prefix="/projects/{project_id}/scans", tags=["scans"])


def _resolve_scan_policy(
    db: Session,
    project: Project,
    policy_id: Optional[UUID],
):
    if policy_id:
        policy = crud_scan_policy.get_scan_policy(db=db, policy_id=policy_id)
        if not policy or policy.project_id != project.id:
            raise HTTPException(status_code=404, detail="Scan policy not found")
        if not policy.enabled:
            raise HTTPException(status_code=400, detail="Scan policy is disabled")
        return policy

    policy = crud_scan_policy.get_default_policy(db=db, project_id=project.id)
    if policy and not policy.enabled:
        return None
    return policy


def _merge_scan_config(policy, config: dict) -> dict:
    merged = dict((policy.scan_config or {}) if policy else {})
    merged.update(config or {})
    return merged


def _to_celery_priority(priority: int) -> int:
    """
    Convert API priority range (1-10) to Celery priority range (0-9).
    """
    normalized = max(1, min(10, int(priority or 5)))
    return normalized - 1


def _dispatch_scan_task(task):
    celery_priority = _to_celery_priority(task.priority)
    task_id = str(task.id)

    task_type = task.task_type
    if task_type in ("subdomain_scan", "dns_resolve", "port_scan"):
        scan_tasks.run_scan.apply_async(args=[task_id], priority=celery_priority)
    elif task_type == "http_probe":
        http_probe_tasks.run_http_probe.apply_async(args=[task_id], priority=celery_priority)
    elif task_type == "fingerprint":
        fingerprint_tasks.run_fingerprint.apply_async(args=[task_id], priority=celery_priority)
    elif task_type == "screenshot":
        screenshot_tasks.run_screenshot.apply_async(args=[task_id], priority=celery_priority)
    elif task_type == "nuclei_scan":
        nuclei_tasks.run_nuclei_scan.apply_async(args=[task_id], priority=celery_priority)
    elif task_type == "xray_scan":
        xray_tasks.run_xray_scan.apply_async(args=[task_id], priority=celery_priority)
    elif task_type == "js_api_discovery":
        js_api_discovery_tasks.run_js_api_discovery.apply_async(
            args=[task_id],
            priority=celery_priority,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown task type: {task_type}")


@router.post("", response_model=ScanTaskOut, status_code=201)
def create_scan(
    body: ScanTaskCreate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    policy = _resolve_scan_policy(db=db, project=project, policy_id=body.policy_id)
    merged_config = _merge_scan_config(policy=policy, config=body.config)

    task = crud_scan_task.create_scan_task(
        db=db,
        project_id=project.id,
        task_type=body.task_type.value,
        config=merged_config,
        priority=body.priority,
        scan_policy_id=policy.id if policy else None,
    )
    return task


@router.get("", response_model=Page[ScanTaskOut])
def list_scans(
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 100:
        limit = 20
    tasks = crud_scan_task.list_scan_tasks(
        db=db,
        project_id=project.id,
        task_type=task_type,
        status=status,
        skip=skip,
        limit=limit,
    )
    total = crud_scan_task.count_scan_tasks(
        db=db,
        project_id=project.id,
        task_type=task_type,
        status=status,
    )
    return Page(items=tasks, total=total, skip=skip, limit=limit)


@router.get("/{task_id}", response_model=ScanTaskOut)
def get_scan(
    task_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    task = crud_scan_task.get_scan_task(db=db, task_id=task_id)
    if not task or task.project_id != project.id:
        raise HTTPException(status_code=404, detail="Scan task not found")
    return task


@router.post("/{task_id}/start", response_model=ScanTaskOut)
def start_scan(
    task_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    task = crud_scan_task.get_scan_task(db=db, task_id=task_id)
    if not task or task.project_id != project.id:
        raise HTTPException(status_code=404, detail="Scan task not found")
    if task.status != "pending":
        raise HTTPException(status_code=400, detail="Task is not in pending status")

    started_task = crud_scan_task.start_scan_task(
        db=db,
        task_id=task.id,
        project_id=project.id,
    )
    if not started_task:
        raise HTTPException(status_code=409, detail="Task was already started")

    try:
        _dispatch_scan_task(started_task)
    except Exception as exc:
        crud_scan_task.update_scan_task_status(
            db=db,
            task_id=started_task.id,
            status="failed",
            error_message=f"Task dispatch failed: {exc}",
        )
        raise HTTPException(status_code=500, detail=f"Task dispatch failed: {exc}") from exc

    return started_task
