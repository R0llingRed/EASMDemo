from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class WebAssetOut(BaseModel):
    id: UUID
    project_id: UUID
    url: str
    subdomain_id: Optional[UUID] = None
    ip_id: Optional[UUID] = None
    port_id: Optional[UUID] = None
    title: Optional[str] = None
    status_code: Optional[int] = None
    content_length: Optional[int] = None
    content_type: Optional[str] = None
    server: Optional[str] = None
    technologies: List[str]
    fingerprints: List[str]
    screenshot_path: Optional[str] = None
    is_alive: bool
    first_seen: datetime
    last_seen: datetime

    model_config = {"from_attributes": True}
