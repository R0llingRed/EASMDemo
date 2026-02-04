import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from server.app.db.base import Base


class EventTrigger(Base):
    """事件触发器模型 - 定义事件到DAG的映射"""

    __tablename__ = "event_trigger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    # 事件类型: asset_created, asset_updated, scan_completed, subdomain_discovered, etc.
    event_type = Column(String(64), nullable=False, index=True)
    # 事件过滤条件: {"asset_type": "subdomain", "severity": ["high", "critical"]}
    filter_config = Column(JSONB, default=dict)
    # 触发的DAG模板
    dag_template_id = Column(
        UUID(as_uuid=True), ForeignKey("dag_template.id"), nullable=False, index=True
    )
    # 传递给DAG的额外配置
    dag_config = Column(JSONB, default=dict)
    enabled = Column(Boolean, default=True, index=True)
    # 触发次数统计
    trigger_count = Column(JSONB, default={"total": 0, "success": 0, "failed": 0})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
