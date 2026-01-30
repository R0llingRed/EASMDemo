from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    subdomain_scan = "subdomain_scan"
    dns_resolve = "dns_resolve"
    port_scan = "port_scan"
    http_probe = "http_probe"
    fingerprint = "fingerprint"
    screenshot = "screenshot"
    nuclei_scan = "nuclei_scan"
    xray_scan = "xray_scan"


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ScanTaskCreate(BaseModel):
    task_type: TaskType
    config: Dict[str, Any] = Field(default_factory=dict)


class ScanTaskOut(BaseModel):
    id: UUID
    project_id: UUID
    task_type: str
    status: str
    progress: int
    total_targets: int
    completed_targets: int
    config: Dict[str, Any]
    result_summary: Dict[str, Any]
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
