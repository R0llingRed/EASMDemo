import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from server.app.db.base import Base


class DAGTemplate(Base):
    """DAG模板模型 - 定义任务依赖图模板"""

    __tablename__ = "dag_template"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("project.id"), nullable=True, index=True
    )  # NULL = 全局模板
    name = Column(String(255), nullable=False)
    description = Column(Text)
    # 节点定义: [{"id": "subdomain", "task_type": "subdomain_scan", "config": {}}]
    nodes = Column(JSONB, nullable=False, default=list)
    # 边定义（可选，也可从nodes的depends_on推断）
    edges = Column(JSONB, default=list)
    is_system = Column(Boolean, default=False, index=True)  # 是否为系统预置模板
    enabled = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
