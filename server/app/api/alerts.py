"""
Alert API Routes
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud import alert as crud_alert
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.alert import (
    AlertAcknowledgeRequest,
    AlertPolicyCreate,
    AlertPolicyOut,
    AlertPolicyUpdate,
    AlertRecordOut,
    AlertResolveRequest,
    AlertSeverity,
    AlertStatus,
)
from server.app.schemas.common import Page

router = APIRouter(prefix="/projects/{project_id}/alerts", tags=["alerts"])


# Alert Policies
@router.get("/policies", response_model=Page[AlertPolicyOut])
def list_alert_policies(
    enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """列出告警策略"""
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 100:
        limit = 20
    
    items = crud_alert.list_alert_policies(
        db=db,
        project_id=project.id,
        enabled=enabled,
        skip=skip,
        limit=limit,
    )
    total = crud_alert.count_alert_policies(db=db, project_id=project.id, enabled=enabled)
    return Page(items=items, total=total, skip=skip, limit=limit)


@router.post("/policies", response_model=AlertPolicyOut, status_code=201)
def create_alert_policy(
    body: AlertPolicyCreate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """创建告警策略"""
    # 验证通知渠道存在
    for channel_id in body.channel_ids:
        channel = crud_alert.get_notification_channel(db=db, channel_id=channel_id)
        if not channel or channel.project_id != project.id:
            raise HTTPException(status_code=400, detail=f"Notification channel {channel_id} not found")
    
    policy = crud_alert.create_alert_policy(
        db=db,
        project_id=project.id,
        name=body.name,
        description=body.description,
        conditions=body.conditions,
        severity_threshold=body.severity_threshold.value,
        channel_ids=[str(cid) for cid in body.channel_ids],
        notification_template=body.notification_template,
        cooldown_minutes=body.cooldown_minutes,
        aggregation_window=body.aggregation_window,
        max_alerts_per_hour=body.max_alerts_per_hour,
        enabled=body.enabled,
    )
    return policy


@router.get("/policies/{policy_id}", response_model=AlertPolicyOut)
def get_alert_policy(
    policy_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """获取告警策略"""
    policy = crud_alert.get_alert_policy(db=db, policy_id=policy_id)
    if not policy or policy.project_id != project.id:
        raise HTTPException(status_code=404, detail="Alert policy not found")
    return policy


@router.patch("/policies/{policy_id}", response_model=AlertPolicyOut)
def update_alert_policy(
    policy_id: UUID,
    body: AlertPolicyUpdate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """更新告警策略"""
    policy = crud_alert.get_alert_policy(db=db, policy_id=policy_id)
    if not policy or policy.project_id != project.id:
        raise HTTPException(status_code=404, detail="Alert policy not found")
    
    update_data = body.model_dump(exclude_unset=True)
    if "severity_threshold" in update_data and update_data["severity_threshold"]:
        update_data["severity_threshold"] = update_data["severity_threshold"].value
    if "channel_ids" in update_data and update_data["channel_ids"]:
        update_data["channel_ids"] = [str(cid) for cid in update_data["channel_ids"]]
    
    updated = crud_alert.update_alert_policy(db=db, policy=policy, **update_data)
    return updated


@router.delete("/policies/{policy_id}", status_code=204)
def delete_alert_policy(
    policy_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """删除告警策略"""
    policy = crud_alert.get_alert_policy(db=db, policy_id=policy_id)
    if not policy or policy.project_id != project.id:
        raise HTTPException(status_code=404, detail="Alert policy not found")
    crud_alert.delete_alert_policy(db=db, policy=policy)
    return None


# Alert Records
@router.get("", response_model=Page[AlertRecordOut])
def list_alert_records(
    policy_id: Optional[UUID] = None,
    status: Optional[AlertStatus] = None,
    severity: Optional[AlertSeverity] = None,
    skip: int = 0,
    limit: int = 20,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """列出告警记录"""
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 100:
        limit = 20
    
    status_str = status.value if status else None
    severity_str = severity.value if severity else None
    
    items = crud_alert.list_alert_records(
        db=db,
        project_id=project.id,
        policy_id=policy_id,
        status=status_str,
        severity=severity_str,
        skip=skip,
        limit=limit,
    )
    total = crud_alert.count_alert_records(
        db=db,
        project_id=project.id,
        policy_id=policy_id,
        status=status_str,
        severity=severity_str,
    )
    return Page(items=items, total=total, skip=skip, limit=limit)


@router.get("/{alert_id}", response_model=AlertRecordOut)
def get_alert_record(
    alert_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """获取告警记录"""
    record = crud_alert.get_alert_record(db=db, record_id=alert_id)
    if not record or record.project_id != project.id:
        raise HTTPException(status_code=404, detail="Alert record not found")
    return record


@router.post("/{alert_id}/acknowledge", response_model=AlertRecordOut)
def acknowledge_alert(
    alert_id: UUID,
    body: AlertAcknowledgeRequest,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """确认告警"""
    record = crud_alert.get_alert_record(db=db, record_id=alert_id)
    if not record or record.project_id != project.id:
        raise HTTPException(status_code=404, detail="Alert record not found")
    if record.status not in ["pending", "sent"]:
        raise HTTPException(status_code=400, detail="Alert cannot be acknowledged in current status")
    
    updated = crud_alert.update_alert_status(
        db=db,
        record=record,
        status="acknowledged",
        acknowledged_by=body.acknowledged_by,
    )
    return updated


@router.post("/{alert_id}/resolve", response_model=AlertRecordOut)
def resolve_alert(
    alert_id: UUID,
    body: AlertResolveRequest,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """解决告警"""
    record = crud_alert.get_alert_record(db=db, record_id=alert_id)
    if not record or record.project_id != project.id:
        raise HTTPException(status_code=404, detail="Alert record not found")
    if record.status == "resolved":
        raise HTTPException(status_code=400, detail="Alert is already resolved")
    
    updated = crud_alert.update_alert_status(db=db, record=record, status="resolved")
    return updated
