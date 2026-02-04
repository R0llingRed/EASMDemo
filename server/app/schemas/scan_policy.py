from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ScanPolicyCreate(BaseModel):
    """创建扫描策略"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scan_config: Dict[str, Any] = Field(default_factory=dict)
    dag_template_id: Optional[UUID] = None
    is_default: bool = False
    enabled: bool = True


class ScanPolicyUpdate(BaseModel):
    """更新扫描策略"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scan_config: Optional[Dict[str, Any]] = None
    dag_template_id: Optional[UUID] = None
    is_default: Optional[bool] = None
    enabled: Optional[bool] = None


class ScanPolicyOut(BaseModel):
    """扫描策略输出"""

    id: UUID
    project_id: UUID
    name: str
    description: Optional[str] = None
    scan_config: Dict[str, Any]
    dag_template_id: Optional[UUID] = None
    is_default: bool
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
