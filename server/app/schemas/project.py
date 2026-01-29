from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
