from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from server.app.models.event_trigger import EventTrigger


def create_event_trigger(
    db: Session,
    project_id: UUID,
    name: str,
    event_type: str,
    dag_template_id: UUID,
    description: Optional[str] = None,
    filter_config: Optional[dict] = None,
    dag_config: Optional[dict] = None,
    enabled: bool = True,
) -> EventTrigger:
    """创建事件触发器"""
    trigger = EventTrigger(
        project_id=project_id,
        name=name,
        description=description,
        event_type=event_type,
        filter_config=filter_config or {},
        dag_template_id=dag_template_id,
        dag_config=dag_config or {},
        enabled=enabled,
    )
    db.add(trigger)
    db.commit()
    db.refresh(trigger)
    return trigger


def get_event_trigger(db: Session, trigger_id: UUID) -> Optional[EventTrigger]:
    """获取事件触发器"""
    return db.query(EventTrigger).filter(EventTrigger.id == trigger_id).first()


def list_event_triggers(
    db: Session,
    project_id: UUID,
    event_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[EventTrigger]:
    """列出事件触发器"""
    query = db.query(EventTrigger).filter(EventTrigger.project_id == project_id)
    if event_type:
        query = query.filter(EventTrigger.event_type == event_type)
    if enabled is not None:
        query = query.filter(EventTrigger.enabled == enabled)
    return query.order_by(EventTrigger.created_at.desc()).offset(skip).limit(limit).all()


def count_event_triggers(
    db: Session,
    project_id: UUID,
    event_type: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> int:
    """统计事件触发器数量"""
    query = db.query(EventTrigger).filter(EventTrigger.project_id == project_id)
    if event_type:
        query = query.filter(EventTrigger.event_type == event_type)
    if enabled is not None:
        query = query.filter(EventTrigger.enabled == enabled)
    return query.count()


def get_triggers_by_event_type(
    db: Session,
    project_id: UUID,
    event_type: str,
) -> List[EventTrigger]:
    """获取指定事件类型的所有启用触发器"""
    return (
        db.query(EventTrigger)
        .filter(
            EventTrigger.project_id == project_id,
            EventTrigger.event_type == event_type,
            EventTrigger.enabled == True,
        )
        .all()
    )


def update_event_trigger(
    db: Session,
    trigger: EventTrigger,
    **kwargs,
) -> EventTrigger:
    """更新事件触发器"""
    for key, value in kwargs.items():
        if value is not None and hasattr(trigger, key):
            setattr(trigger, key, value)
    db.commit()
    db.refresh(trigger)
    return trigger


def increment_trigger_count(
    db: Session,
    trigger: EventTrigger,
    success: bool = True,
) -> EventTrigger:
    """
    增加触发计数（带行级锁防止并发问题）
    """
    # 使用 SELECT FOR UPDATE 获取行级锁
    locked_trigger = db.query(EventTrigger).filter(
        EventTrigger.id == trigger.id
    ).with_for_update().first()
    
    if not locked_trigger:
        db.refresh(trigger)
        return trigger
    
    counts = dict(locked_trigger.trigger_count) if locked_trigger.trigger_count else {"total": 0, "success": 0, "failed": 0}
    counts["total"] = counts.get("total", 0) + 1
    if success:
        counts["success"] = counts.get("success", 0) + 1
    else:
        counts["failed"] = counts.get("failed", 0) + 1
    locked_trigger.trigger_count = counts
    db.commit()
    db.refresh(locked_trigger)
    return locked_trigger


def delete_event_trigger(db: Session, trigger: EventTrigger) -> None:
    """删除事件触发器"""
    db.delete(trigger)
    db.commit()
