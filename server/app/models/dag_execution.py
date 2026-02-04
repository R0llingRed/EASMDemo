import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from server.app.db.base import Base


class DAGExecution(Base):
    """DAG执行实例模型 - 记录每次DAG执行的状态"""

    __tablename__ = "dag_execution"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False, index=True)
    dag_template_id = Column(
        UUID(as_uuid=True), ForeignKey("dag_template.id"), nullable=False, index=True
    )
    # 触发类型: manual(手动), event(事件触发), schedule(定时)
    trigger_type = Column(String(32), nullable=False, default="manual")
    # 触发事件详情
    trigger_event = Column(JSONB, default=dict)
    # 状态: pending, running, completed, failed, cancelled
    status = Column(String(32), nullable=False, default="pending", index=True)
    # 各节点状态: {"subdomain": "completed", "dns": "running", "port": "pending"}
    node_states = Column(JSONB, default=dict)
    # 各节点对应的scan_task_id: {"subdomain": "uuid", "dns": "uuid"}
    node_task_ids = Column(JSONB, default=dict)
    # 输入配置（启动时传入的参数）
    input_config = Column(JSONB, default=dict)
    # 错误信息
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
