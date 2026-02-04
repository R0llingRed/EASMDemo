import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from server.app.db.base import Base


class ScanPolicy(Base):
    """扫描策略模型 - 管理项目级别的扫描策略配置"""

    __tablename__ = "scan_policy"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    scan_config = Column(JSONB, default=dict)  # 扫描配置（速率、范围、工具链）
    dag_template_id = Column(UUID(as_uuid=True), ForeignKey("dag_template.id"), nullable=True)
    is_default = Column(Boolean, default=False, index=True)
    enabled = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
