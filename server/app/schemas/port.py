from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PortOut(BaseModel):
    id: UUID
    ip_id: UUID
    port: int
    protocol: str
    state: Optional[str] = None
    service: Optional[str] = None
    version: Optional[str] = None
    banner: Optional[str] = None
    first_seen: datetime
    last_seen: datetime

    model_config = {"from_attributes": True}
