"""
Alert Schemas - Pydantic models for alerting system
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class AlertStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    acknowledged = "acknowledged"
    resolved = "resolved"


class ChannelType(str, Enum):
    email = "email"
    webhook = "webhook"
    dingtalk = "dingtalk"
    feishu = "feishu"
    wechat = "wechat"


# Notification Channel Schemas
class NotificationChannelCreate(BaseModel):
    """创建通知渠道"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    channel_type: ChannelType
    config: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class NotificationChannelUpdate(BaseModel):
    """更新通知渠道"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class NotificationChannelOut(BaseModel):
    """通知渠道输出"""
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str] = None
    channel_type: str
    config: Dict[str, Any]  # 敏感字段应在API层脱敏
    enabled: bool
    last_test_at: Optional[datetime] = None
    last_test_success: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Alert Policy Schemas
class AlertPolicyCreate(BaseModel):
    """创建告警策略"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    conditions: Dict[str, Any] = Field(default_factory=dict)
    severity_threshold: AlertSeverity = AlertSeverity.high
    channel_ids: List[UUID] = Field(default_factory=list)
    notification_template: Optional[str] = None
    cooldown_minutes: int = Field(default=60, ge=0, le=1440)
    aggregation_window: int = Field(default=5, ge=0, le=60)
    max_alerts_per_hour: int = Field(default=10, ge=1, le=100)
    enabled: bool = True


class AlertPolicyUpdate(BaseModel):
    """更新告警策略"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    severity_threshold: Optional[AlertSeverity] = None
    channel_ids: Optional[List[UUID]] = None
    notification_template: Optional[str] = None
    cooldown_minutes: Optional[int] = Field(None, ge=0, le=1440)
    aggregation_window: Optional[int] = Field(None, ge=0, le=60)
    max_alerts_per_hour: Optional[int] = Field(None, ge=1, le=100)
    enabled: Optional[bool] = None


class AlertPolicyOut(BaseModel):
    """告警策略输出"""
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str] = None
    conditions: Dict[str, Any]
    severity_threshold: str
    channel_ids: List[UUID]
    notification_template: Optional[str] = None
    cooldown_minutes: int
    aggregation_window: int
    max_alerts_per_hour: int
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Alert Record Schemas
class AlertRecordOut(BaseModel):
    """告警记录输出"""
    id: UUID
    project_id: UUID
    policy_id: Optional[UUID] = None
    target_type: str
    target_id: Optional[UUID] = None
    title: str
    message: str
    severity: str
    details: Dict[str, Any]
    status: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    notification_results: Dict[str, Any]
    aggregated_count: int
    created_at: datetime
    sent_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AlertAcknowledgeRequest(BaseModel):
    """确认告警请求"""
    acknowledged_by: str = Field(..., min_length=1, max_length=255)
    notes: Optional[str] = None


class AlertResolveRequest(BaseModel):
    """解决告警请求"""
    resolution_notes: Optional[str] = None
