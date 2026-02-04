from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud import dag_template as crud_template
from server.app.crud import event_trigger as crud_trigger
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.common import Page
from server.app.schemas.event_trigger import (
    EventPayload,
    EventTriggerCreate,
    EventTriggerOut,
    EventTriggerUpdate,
    EventType,
)
from worker.app.tasks import event_handler

router = APIRouter(prefix="/projects/{project_id}/event-triggers", tags=["event-triggers"])


@router.post("", response_model=EventTriggerOut, status_code=201)
def create_trigger(
    body: EventTriggerCreate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """创建事件触发器"""
    # 验证DAG模板存在
    template = crud_template.get_dag_template(db=db, template_id=body.dag_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="DAG template not found")
    if template.project_id and template.project_id != project.id:
        raise HTTPException(status_code=404, detail="DAG template not found")

    trigger = crud_trigger.create_event_trigger(
        db=db,
        project_id=project.id,
        name=body.name,
        description=body.description,
        event_type=body.event_type.value,
        filter_config=body.filter_config,
        dag_template_id=body.dag_template_id,
        dag_config=body.dag_config,
        enabled=body.enabled,
    )
    return trigger


@router.get("", response_model=Page[EventTriggerOut])
def list_triggers(
    event_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """列出事件触发器"""
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 100:
        limit = 20
    items = crud_trigger.list_event_triggers(
        db=db,
        project_id=project.id,
        event_type=event_type,
        enabled=enabled,
        skip=skip,
        limit=limit,
    )
    total = crud_trigger.count_event_triggers(
        db=db,
        project_id=project.id,
        event_type=event_type,
        enabled=enabled,
    )
    return Page(items=items, total=total, skip=skip, limit=limit)


@router.get("/{trigger_id}", response_model=EventTriggerOut)
def get_trigger(
    trigger_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """获取事件触发器"""
    trigger = crud_trigger.get_event_trigger(db=db, trigger_id=trigger_id)
    if not trigger or trigger.project_id != project.id:
        raise HTTPException(status_code=404, detail="Trigger not found")
    return trigger


@router.patch("/{trigger_id}", response_model=EventTriggerOut)
def update_trigger(
    trigger_id: UUID,
    body: EventTriggerUpdate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """更新事件触发器"""
    trigger = crud_trigger.get_event_trigger(db=db, trigger_id=trigger_id)
    if not trigger or trigger.project_id != project.id:
        raise HTTPException(status_code=404, detail="Trigger not found")

    # 如果更新DAG模板，验证其存在
    if body.dag_template_id:
        template = crud_template.get_dag_template(db=db, template_id=body.dag_template_id)
        if not template:
            raise HTTPException(status_code=404, detail="DAG template not found")
        if template.project_id and template.project_id != project.id:
            raise HTTPException(status_code=404, detail="DAG template not found")

    update_data = body.model_dump(exclude_unset=True)
    if "event_type" in update_data and update_data["event_type"]:
        update_data["event_type"] = update_data["event_type"].value

    updated = crud_trigger.update_event_trigger(db=db, trigger=trigger, **update_data)
    return updated


@router.delete("/{trigger_id}", status_code=204)
def delete_trigger(
    trigger_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """删除事件触发器"""
    trigger = crud_trigger.get_event_trigger(db=db, trigger_id=trigger_id)
    if not trigger or trigger.project_id != project.id:
        raise HTTPException(status_code=404, detail="Trigger not found")
    crud_trigger.delete_event_trigger(db=db, trigger=trigger)
    return None


# 事件发送接口
events_router = APIRouter(prefix="/projects/{project_id}/events", tags=["events"])


@events_router.post("/emit", status_code=202)
def emit_event(
    body: EventPayload,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """发送事件（触发匹配的事件触发器）"""
    if body.project_id != project.id:
        raise HTTPException(status_code=400, detail="Project ID mismatch")

    # 异步处理事件
    event_handler.process_event.delay(
        project_id=str(project.id),
        event_type=body.event_type.value,
        event_data=body.data,
    )

    return {"message": "Event emitted", "event_type": body.event_type.value}
