from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud import scan_task as crud_scan_task
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.common import Page
from server.app.schemas.scan_task import ScanTaskCreate, ScanTaskOut
from worker.app.tasks import fingerprint as fingerprint_tasks
from worker.app.tasks import http_probe as http_probe_tasks
from worker.app.tasks import scan as scan_tasks
from worker.app.tasks import screenshot as screenshot_tasks

router = APIRouter(prefix="/projects/{project_id}/scans", tags=["scans"])


@router.post("", response_model=ScanTaskOut, status_code=201)
def create_scan(
    body: ScanTaskCreate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    task = crud_scan_task.create_scan_task(
        db=db,
        project_id=project.id,
        task_type=body.task_type.value,
        config=body.config,
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

    # Dispatch to the correct Celery task based on task_type
    task_type = task.task_type
    if task_type in ("subdomain_scan", "dns_resolve", "port_scan"):
        scan_tasks.run_scan.delay(str(task.id))
    elif task_type == "http_probe":
        http_probe_tasks.run_http_probe.delay(str(task.id))
    elif task_type == "fingerprint":
        fingerprint_tasks.run_fingerprint.delay(str(task.id))
    elif task_type == "screenshot":
        screenshot_tasks.run_screenshot.delay(str(task.id))
    else:
        raise HTTPException(status_code=400, detail=f"Unknown task type: {task_type}")

    return task
