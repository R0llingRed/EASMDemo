"""Schemas for JS deep analysis and API endpoint findings."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class JSAssetOut(BaseModel):
    id: UUID
    project_id: UUID
    web_asset_id: Optional[UUID] = None
    script_url: str
    script_type: str
    content_hash: str
    source_url: Optional[str] = None
    scan_metadata: Dict[str, Any]
    first_seen: datetime
    last_seen: datetime

    model_config = {"from_attributes": True}


class APIEndpointOut(BaseModel):
    id: UUID
    project_id: UUID
    js_asset_id: Optional[UUID] = None
    endpoint: str
    method: str
    host: Optional[str] = None
    source: str
    requires_auth: Optional[bool] = None
    risk_tags: List[str]
    evidence: Dict[str, Any]
    first_seen: datetime
    last_seen: datetime

    model_config = {"from_attributes": True}


class APIRiskFindingOut(BaseModel):
    id: UUID
    project_id: UUID
    endpoint_id: Optional[UUID] = None
    rule_name: str
    severity: str
    title: str
    description: Optional[str] = None
    evidence: Dict[str, Any]
    status: str
    updated_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    status_history: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class APIRiskStatus(str, Enum):
    open = "open"
    investigating = "investigating"
    accepted_risk = "accepted_risk"
    resolved = "resolved"
    false_positive = "false_positive"


class APIRiskStatusUpdate(BaseModel):
    status: APIRiskStatus
    updated_by: str
    resolution_notes: Optional[str] = None
