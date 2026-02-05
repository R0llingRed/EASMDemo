"""
Notification Channel API Routes
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
    ChannelType,
    NotificationChannelCreate,
    NotificationChannelOut,
    NotificationChannelUpdate,
)
from worker.app.tasks import notifier

router = APIRouter(prefix="/projects/{project_id}/notification-channels", tags=["notifications"])


@router.get("", response_model=list[NotificationChannelOut])
def list_notification_channels(
    channel_type: Optional[ChannelType] = None,
    enabled: Optional[bool] = None,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """列出通知渠道"""
    type_str = channel_type.value if channel_type else None
    channels = crud_alert.list_notification_channels(
        db=db,
        project_id=project.id,
        channel_type=type_str,
        enabled=enabled,
    )
    # 脱敏处理敏感配置
    for channel in channels:
        channel.config = _mask_sensitive_config(channel.config)
    return channels


@router.post("", response_model=NotificationChannelOut, status_code=201)
def create_notification_channel(
    body: NotificationChannelCreate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """创建通知渠道"""
    channel = crud_alert.create_notification_channel(
        db=db,
        project_id=project.id,
        name=body.name,
        description=body.description,
        channel_type=body.channel_type.value,
        config=body.config,
        enabled=body.enabled,
    )
    return channel


@router.get("/{channel_id}", response_model=NotificationChannelOut)
def get_notification_channel(
    channel_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """获取通知渠道"""
    channel = crud_alert.get_notification_channel(db=db, channel_id=channel_id)
    if not channel or channel.project_id != project.id:
        raise HTTPException(status_code=404, detail="Notification channel not found")
    channel.config = _mask_sensitive_config(channel.config)
    return channel


@router.patch("/{channel_id}", response_model=NotificationChannelOut)
def update_notification_channel(
    channel_id: UUID,
    body: NotificationChannelUpdate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """更新通知渠道"""
    channel = crud_alert.get_notification_channel(db=db, channel_id=channel_id)
    if not channel or channel.project_id != project.id:
        raise HTTPException(status_code=404, detail="Notification channel not found")
    
    updated = crud_alert.update_notification_channel(db=db, channel=channel, **body.model_dump(exclude_unset=True))
    return updated


@router.delete("/{channel_id}", status_code=204)
def delete_notification_channel(
    channel_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """删除通知渠道"""
    channel = crud_alert.get_notification_channel(db=db, channel_id=channel_id)
    if not channel or channel.project_id != project.id:
        raise HTTPException(status_code=404, detail="Notification channel not found")
    crud_alert.delete_notification_channel(db=db, channel=channel)
    return None


@router.post("/{channel_id}/test", status_code=202)
def test_notification_channel(
    channel_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """测试通知渠道"""
    channel = crud_alert.get_notification_channel(db=db, channel_id=channel_id)
    if not channel or channel.project_id != project.id:
        raise HTTPException(status_code=404, detail="Notification channel not found")
    
    # 异步发送测试通知（安全：不传递敏感配置）
    notifier.test_channel.delay(
        channel_id=str(channel_id),
    )
    
    return {"message": "Test notification sent", "channel_id": str(channel_id)}


def _mask_sensitive_config(config: dict, depth: int = 0) -> dict:
    """
    脱敏敏感配置字段（递归处理嵌套对象）
    
    Args:
        config: 配置字典
        depth: 递归深度（防止无限递归）
    """
    if not config or depth > 5:
        return config
    
    sensitive_keys = ["token", "secret", "password", "api_key", "access_token", "key", "credential"]
    masked = {}
    
    for key, value in config.items():
        if isinstance(value, dict):
            # 递归处理嵌套字典
            masked[key] = _mask_sensitive_config(value, depth + 1)
        elif isinstance(value, list):
            # 处理列表（可能包含嵌套字典）
            masked[key] = [
                _mask_sensitive_config(item, depth + 1) if isinstance(item, dict) else item
                for item in value
            ]
        elif any(sk in key.lower() for sk in sensitive_keys):
            # 脱敏敏感字段
            if isinstance(value, str) and len(value) > 4:
                masked[key] = value[:4] + "****"
            else:
                masked[key] = "****"
        else:
            masked[key] = value
    
    return masked

