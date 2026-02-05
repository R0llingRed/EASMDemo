"""
Alert CRUD Operations
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from server.app.models.alert import AlertPolicy, AlertRecord, NotificationChannel


# Notification Channel CRUD
def create_notification_channel(
    db: Session,
    project_id: UUID,
    name: str,
    channel_type: str,
    config: Optional[dict] = None,
    description: Optional[str] = None,
    enabled: bool = True,
) -> NotificationChannel:
    """创建通知渠道"""
    channel = NotificationChannel(
        project_id=project_id,
        name=name,
        description=description,
        channel_type=channel_type,
        config=config or {},
        enabled=enabled,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


def get_notification_channel(db: Session, channel_id: UUID) -> Optional[NotificationChannel]:
    """获取通知渠道"""
    return db.query(NotificationChannel).filter(NotificationChannel.id == channel_id).first()


def list_notification_channels(
    db: Session,
    project_id: UUID,
    channel_type: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> List[NotificationChannel]:
    """列出通知渠道"""
    query = db.query(NotificationChannel).filter(NotificationChannel.project_id == project_id)
    if channel_type:
        query = query.filter(NotificationChannel.channel_type == channel_type)
    if enabled is not None:
        query = query.filter(NotificationChannel.enabled == enabled)
    return query.order_by(NotificationChannel.created_at.desc()).all()


def update_notification_channel(db: Session, channel: NotificationChannel, **kwargs) -> NotificationChannel:
    """更新通知渠道"""
    for key, value in kwargs.items():
        if value is not None and hasattr(channel, key):
            setattr(channel, key, value)
    db.commit()
    db.refresh(channel)
    return channel


def update_channel_test_result(
    db: Session,
    channel: NotificationChannel,
    success: bool,
) -> NotificationChannel:
    """更新渠道测试结果"""
    channel.last_test_at = datetime.utcnow()
    channel.last_test_success = success
    db.commit()
    db.refresh(channel)
    return channel


def delete_notification_channel(db: Session, channel: NotificationChannel) -> None:
    """删除通知渠道"""
    db.delete(channel)
    db.commit()


# Alert Policy CRUD
def create_alert_policy(
    db: Session,
    project_id: UUID,
    name: str,
    conditions: Optional[dict] = None,
    severity_threshold: str = "high",
    channel_ids: Optional[list] = None,
    description: Optional[str] = None,
    notification_template: Optional[str] = None,
    cooldown_minutes: int = 60,
    aggregation_window: int = 5,
    max_alerts_per_hour: int = 10,
    enabled: bool = True,
) -> AlertPolicy:
    """创建告警策略"""
    policy = AlertPolicy(
        project_id=project_id,
        name=name,
        description=description,
        conditions=conditions or {},
        severity_threshold=severity_threshold,
        channel_ids=channel_ids or [],
        notification_template=notification_template,
        cooldown_minutes=cooldown_minutes,
        aggregation_window=aggregation_window,
        max_alerts_per_hour=max_alerts_per_hour,
        enabled=enabled,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def get_alert_policy(db: Session, policy_id: UUID) -> Optional[AlertPolicy]:
    """获取告警策略"""
    return db.query(AlertPolicy).filter(AlertPolicy.id == policy_id).first()


def list_alert_policies(
    db: Session,
    project_id: UUID,
    enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[AlertPolicy]:
    """列出告警策略"""
    query = db.query(AlertPolicy).filter(AlertPolicy.project_id == project_id)
    if enabled is not None:
        query = query.filter(AlertPolicy.enabled == enabled)
    return query.order_by(AlertPolicy.created_at.desc()).offset(skip).limit(limit).all()


def count_alert_policies(db: Session, project_id: UUID, enabled: Optional[bool] = None) -> int:
    """统计告警策略数量"""
    query = db.query(AlertPolicy).filter(AlertPolicy.project_id == project_id)
    if enabled is not None:
        query = query.filter(AlertPolicy.enabled == enabled)
    return query.count()


def update_alert_policy(db: Session, policy: AlertPolicy, **kwargs) -> AlertPolicy:
    """更新告警策略"""
    for key, value in kwargs.items():
        if value is not None and hasattr(policy, key):
            setattr(policy, key, value)
    db.commit()
    db.refresh(policy)
    return policy


def delete_alert_policy(db: Session, policy: AlertPolicy) -> None:
    """删除告警策略"""
    db.delete(policy)
    db.commit()


# Alert Record CRUD
def create_alert_record(
    db: Session,
    project_id: UUID,
    title: str,
    message: str,
    severity: str,
    target_type: str,
    policy_id: Optional[UUID] = None,
    target_id: Optional[UUID] = None,
    details: Optional[dict] = None,
    aggregation_key: Optional[str] = None,
) -> AlertRecord:
    """创建告警记录"""
    record = AlertRecord(
        project_id=project_id,
        policy_id=policy_id,
        target_type=target_type,
        target_id=target_id,
        title=title,
        message=message,
        severity=severity,
        details=details or {},
        status="pending",
        aggregation_key=aggregation_key,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_alert_record(db: Session, record_id: UUID) -> Optional[AlertRecord]:
    """获取告警记录"""
    return db.query(AlertRecord).filter(AlertRecord.id == record_id).first()


def list_alert_records(
    db: Session,
    project_id: UUID,
    policy_id: Optional[UUID] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[AlertRecord]:
    """列出告警记录"""
    query = db.query(AlertRecord).filter(AlertRecord.project_id == project_id)
    if policy_id:
        query = query.filter(AlertRecord.policy_id == policy_id)
    if status:
        query = query.filter(AlertRecord.status == status)
    if severity:
        query = query.filter(AlertRecord.severity == severity)
    return query.order_by(AlertRecord.created_at.desc()).offset(skip).limit(limit).all()


def count_alert_records(
    db: Session,
    project_id: UUID,
    policy_id: Optional[UUID] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
) -> int:
    """统计告警记录数量"""
    query = db.query(AlertRecord).filter(AlertRecord.project_id == project_id)
    if policy_id:
        query = query.filter(AlertRecord.policy_id == policy_id)
    if status:
        query = query.filter(AlertRecord.status == status)
    if severity:
        query = query.filter(AlertRecord.severity == severity)
    return query.count()


def find_aggregatable_alert(
    db: Session,
    project_id: UUID,
    aggregation_key: str,
    window_minutes: int,
) -> Optional[AlertRecord]:
    """查找可聚合的告警"""
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
    return db.query(AlertRecord).filter(
        AlertRecord.project_id == project_id,
        AlertRecord.aggregation_key == aggregation_key,
        AlertRecord.created_at >= cutoff,
        AlertRecord.status.in_(["pending", "sent"]),
    ).first()


def increment_aggregated_count(db: Session, record: AlertRecord) -> AlertRecord:
    """增加聚合计数"""
    record.aggregated_count += 1
    db.commit()
    db.refresh(record)
    return record


def update_alert_status(
    db: Session,
    record: AlertRecord,
    status: str,
    acknowledged_by: Optional[str] = None,
) -> AlertRecord:
    """更新告警状态"""
    record.status = status
    if status == "sent" and not record.sent_at:
        record.sent_at = datetime.utcnow()
    elif status == "acknowledged":
        record.acknowledged_at = datetime.utcnow()
        record.acknowledged_by = acknowledged_by
    elif status == "resolved":
        record.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record


def update_notification_results(
    db: Session,
    record: AlertRecord,
    channel_id: str,
    success: bool,
    error: Optional[str] = None,
) -> AlertRecord:
    """更新通知发送结果"""
    results = dict(record.notification_results) if record.notification_results else {}
    results[channel_id] = {
        "success": success,
        "error": error,
        "sent_at": datetime.utcnow().isoformat(),
    }
    record.notification_results = results
    db.commit()
    db.refresh(record)
    return record


def count_recent_alerts(db: Session, project_id: UUID, policy_id: UUID, hours: int = 1) -> int:
    """统计最近时间内的告警数量"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    return db.query(AlertRecord).filter(
        AlertRecord.project_id == project_id,
        AlertRecord.policy_id == policy_id,
        AlertRecord.created_at >= cutoff,
    ).count()


def check_cooldown(
    db: Session,
    project_id: UUID,
    aggregation_key: str,
    cooldown_minutes: int,
) -> bool:
    """检查是否在冷却期内"""
    cutoff = datetime.utcnow() - timedelta(minutes=cooldown_minutes)
    exists = db.query(AlertRecord).filter(
        AlertRecord.project_id == project_id,
        AlertRecord.aggregation_key == aggregation_key,
        AlertRecord.created_at >= cutoff,
    ).first()
    return exists is not None
