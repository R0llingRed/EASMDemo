from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DAGNodeSchema(BaseModel):
    """DAG节点定义"""

    id: str = Field(..., description="节点唯一标识")
    task_type: str = Field(..., description="任务类型")
    depends_on: List[str] = Field(default_factory=list, description="依赖的节点ID列表")
    config: Dict[str, Any] = Field(default_factory=dict, description="节点配置")


class DAGTemplateCreate(BaseModel):
    """创建DAG模板"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: List[DAGNodeSchema] = Field(default_factory=list)
    edges: List[Dict[str, str]] = Field(default_factory=list)  # [{"from": "a", "to": "b"}]
    is_system: bool = False
    enabled: bool = True


class DAGTemplateUpdate(BaseModel):
    """更新DAG模板"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: Optional[List[DAGNodeSchema]] = None
    edges: Optional[List[Dict[str, str]]] = None
    enabled: Optional[bool] = None


class DAGTemplateOut(BaseModel):
    """DAG模板输出"""

    id: UUID
    project_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, str]]
    is_system: bool
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
