"""
Alert Models - Alert policies, records, and notification channels

This module defines models for managing alert policies, tracking alert
records, and configuring multi-channel notifications.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from server.app.db.session import Base


class NotificationChannel(Base):
    """通知渠道配置"""

    __tablename__ = "notification_channels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    channel_type = Column(String(50), nullable=False)  # email, webhook, dingtalk, feishu, wechat
    config = Column(JSONB, nullable=False, default=dict)  # 渠道配置（加密存储敏感信息）
    enabled = Column(Boolean, nullable=False, default=True)
    last_test_at = Column(DateTime, nullable=True)
    last_test_success = Column(Boolean, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AlertPolicy(Base):
    """告警策略"""

    __tablename__ = "alert_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 触发条件
    conditions = Column(JSONB, nullable=False, default=dict)  # 告警条件配置
    severity_threshold = Column(String(20), nullable=False, default="high")  # 严重度阈值
    
    # 通知配置
    channel_ids = Column(JSONB, nullable=False, default=list)  # 通知渠道ID列表
    notification_template = Column(Text, nullable=True)  # 自定义通知模板
    
    # 告警控制
    cooldown_minutes = Column(Integer, nullable=False, default=60)  # 冷却时间（防止重复告警）
    aggregation_window = Column(Integer, nullable=False, default=5)  # 聚合窗口（分钟）
    max_alerts_per_hour = Column(Integer, nullable=False, default=10)  # 每小时最大告警数
    
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AlertRecord(Base):
    """告警记录"""

    __tablename__ = "alert_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("alert_policies.id", ondelete="SET NULL"), nullable=True)
    
    # 告警目标
    target_type = Column(String(50), nullable=False)  # asset, vulnerability, scan_task, etc.
    target_id = Column(UUID(as_uuid=True), nullable=True)
    
    # 告警内容
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # critical, high, medium, low, info
    details = Column(JSONB, nullable=False, default=dict)  # 详细信息
    
    # 状态
    status = Column(String(20), nullable=False, default="pending")  # pending, sent, acknowledged, resolved
    acknowledged_by = Column(String(255), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # 通知记录
    notification_results = Column(JSONB, nullable=False, default=dict)  # {channel_id: {success, error, sent_at}}
    
    # 聚合信息
    aggregation_key = Column(String(255), nullable=True)  # 用于告警聚合
    aggregated_count = Column(Integer, nullable=False, default=1)  # 聚合的告警数量
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
