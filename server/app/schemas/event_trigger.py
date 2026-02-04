from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """事件类型枚举"""

    asset_created = "asset_created"
    asset_updated = "asset_updated"
    asset_deleted = "asset_deleted"
    subdomain_discovered = "subdomain_discovered"
    ip_discovered = "ip_discovered"
    port_discovered = "port_discovered"
    web_asset_discovered = "web_asset_discovered"
    vulnerability_found = "vulnerability_found"
    scan_completed = "scan_completed"
    scan_failed = "scan_failed"


class EventTriggerCreate(BaseModel):
    """创建事件触发器"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    event_type: EventType
    filter_config: Dict[str, Any] = Field(default_factory=dict)
    dag_template_id: UUID
    dag_config: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class EventTriggerUpdate(BaseModel):
    """更新事件触发器"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    filter_config: Optional[Dict[str, Any]] = None
    dag_template_id: Optional[UUID] = None
    dag_config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class EventTriggerOut(BaseModel):
    """事件触发器输出"""

    id: UUID
    project_id: UUID
    name: str
    description: Optional[str] = None
    event_type: str
    filter_config: Dict[str, Any]
    dag_template_id: UUID
    dag_config: Dict[str, Any]
    enabled: bool
    trigger_count: Dict[str, int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventPayload(BaseModel):
    """事件载荷（用于触发事件）"""

    event_type: EventType
    project_id: UUID
    data: Dict[str, Any] = Field(default_factory=dict)
