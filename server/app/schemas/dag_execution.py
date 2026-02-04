from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TriggerType(str, Enum):
    manual = "manual"
    event = "event"
    schedule = "schedule"


class DAGExecutionStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class DAGExecutionCreate(BaseModel):
    """创建DAG执行实例"""

    dag_template_id: UUID
    trigger_type: TriggerType = TriggerType.manual
    trigger_event: Dict[str, Any] = Field(default_factory=dict)
    input_config: Dict[str, Any] = Field(default_factory=dict)


class DAGExecutionOut(BaseModel):
    """DAG执行实例输出"""

    id: UUID
    project_id: UUID
    dag_template_id: UUID
    trigger_type: str
    trigger_event: Dict[str, Any]
    status: str
    node_states: Dict[str, str]
    node_task_ids: Dict[str, str]
    input_config: Dict[str, Any]
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NodeStateUpdate(BaseModel):
    """节点状态更新"""

    node_id: str
    status: str  # pending, running, completed, failed, skipped
    task_id: Optional[UUID] = None
