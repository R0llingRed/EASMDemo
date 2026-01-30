from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class IPAddressOut(BaseModel):
    id: UUID
    project_id: UUID
    ip: str
    source: Optional[str] = None
    asn: Optional[str] = None
    asn_org: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    is_cdn: bool
    first_seen: datetime
    last_seen: datetime

    model_config = {"from_attributes": True}
