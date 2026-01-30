from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from server.app.models.scan_task import ScanTask


def create_scan_task(
    db: Session,
    project_id: UUID,
    task_type: str,
    config: Dict[str, Any],
    total_targets: int = 0,
) -> ScanTask:
    task = ScanTask(
        project_id=project_id,
        task_type=task_type,
        config=config,
        total_targets=total_targets,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_scan_task(db: Session, task_id: UUID) -> Optional[ScanTask]:
    return db.get(ScanTask, task_id)


def list_scan_tasks(
    db: Session,
    project_id: UUID,
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[ScanTask]:
    stmt = select(ScanTask).where(ScanTask.project_id == project_id)
    if task_type:
        stmt = stmt.where(ScanTask.task_type == task_type)
    if status:
        stmt = stmt.where(ScanTask.status == status)
    stmt = stmt.order_by(ScanTask.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def count_scan_tasks(
    db: Session,
    project_id: UUID,
    task_type: Optional[str] = None,
    status: Optional[str] = None,
) -> int:
    stmt = select(func.count()).select_from(ScanTask).where(ScanTask.project_id == project_id)
    if task_type:
        stmt = stmt.where(ScanTask.task_type == task_type)
    if status:
        stmt = stmt.where(ScanTask.status == status)
    return db.scalar(stmt) or 0


def update_scan_task_status(
    db: Session,
    task_id: UUID,
    status: str,
    error_message: Optional[str] = None,
    result_summary: Optional[Dict[str, Any]] = None,
) -> Optional[ScanTask]:
    task = db.get(ScanTask, task_id)
    if not task:
        return None
    task.status = status
    if status == "running" and not task.started_at:
        task.started_at = datetime.utcnow()
    if status in ("completed", "failed"):
        task.completed_at = datetime.utcnow()
    if error_message:
        task.error_message = error_message
    if result_summary:
        task.result_summary = result_summary
    db.commit()
    db.refresh(task)
    return task


def update_scan_task_progress(
    db: Session,
    task_id: UUID,
    completed_targets: int,
) -> Optional[ScanTask]:
    task = db.get(ScanTask, task_id)
    if not task:
        return None
    task.completed_targets = completed_targets
    if task.total_targets > 0:
        task.progress = int((completed_targets / task.total_targets) * 100)
    db.commit()
    db.refresh(task)
    return task
