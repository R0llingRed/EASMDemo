from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from server.app.models.scan_task import ScanTask


def create_scan_task(
    db: Session,
    project_id: UUID,
    task_type: str,
    config: Dict[str, Any],
    priority: int = 5,
    scan_policy_id: Optional[UUID] = None,
    total_targets: int = 0,
) -> ScanTask:
    task = ScanTask(
        project_id=project_id,
        scan_policy_id=scan_policy_id,
        task_type=task_type,
        priority=priority,
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


def start_scan_task(
    db: Session,
    task_id: UUID,
    project_id: UUID,
) -> Optional[ScanTask]:
    """
    Atomically move a scan task from pending to running.
    Returns the updated task when successful; otherwise None.
    """
    stmt = (
        update(ScanTask)
        .where(
            ScanTask.id == task_id,
            ScanTask.project_id == project_id,
            ScanTask.status == "pending",
        )
        .values(status="running", started_at=datetime.utcnow())
    )
    result = db.execute(stmt)
    db.commit()
    if (result.rowcount or 0) < 1:
        return None
    return db.get(ScanTask, task_id)


def transition_scan_task_status(
    db: Session,
    task_id: UUID,
    project_id: UUID,
    from_statuses: List[str],
    to_status: str,
) -> Optional[ScanTask]:
    values: Dict[str, Any] = {"status": to_status}
    if to_status == "running":
        values["started_at"] = datetime.utcnow()
    if to_status in ("completed", "failed", "cancelled"):
        values["completed_at"] = datetime.utcnow()

    stmt = (
        update(ScanTask)
        .where(
            ScanTask.id == task_id,
            ScanTask.project_id == project_id,
            ScanTask.status.in_(from_statuses),
        )
        .values(**values)
    )
    result = db.execute(stmt)
    db.commit()
    if (result.rowcount or 0) < 1:
        return None
    return db.get(ScanTask, task_id)


def update_scan_task(
    db: Session,
    task: ScanTask,
    config: Optional[Dict[str, Any]] = None,
    priority: Optional[int] = None,
) -> ScanTask:
    if config is not None:
        task.config = config
    if priority is not None:
        task.priority = priority
    db.commit()
    db.refresh(task)
    return task


def delete_scan_task(db: Session, task: ScanTask) -> None:
    db.execute(delete(ScanTask).where(ScanTask.id == task.id))
    db.commit()


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
    # Preserve user-issued cancellation as terminal state.
    if task.status == "cancelled" and status in ("running", "completed", "failed"):
        return task
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
    if task.status == "cancelled":
        return task
    task.completed_targets = completed_targets
    if task.total_targets > 0:
        task.progress = int((completed_targets / task.total_targets) * 100)
    db.commit()
    db.refresh(task)
    return task
