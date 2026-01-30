from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class SubdomainOut(BaseModel):
    id: UUID
    project_id: UUID
    root_domain: str
    subdomain: str
    source: Optional[str] = None
    ip_addresses: List[str]
    cname: Optional[str] = None
    is_cdn: bool
    cdn_provider: Optional[str] = None
    status: str
    first_seen: datetime
    last_seen: datetime

    model_config = {"from_attributes": True}
