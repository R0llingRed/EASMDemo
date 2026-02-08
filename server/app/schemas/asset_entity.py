from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AssetType(str, Enum):
    domain = "domain"
    ip = "ip"
    url = "url"


class AssetEntityCreate(BaseModel):
    asset_type: AssetType
    value: str = Field(min_length=1, max_length=2048)
    source: Optional[str] = Field(default=None, max_length=128)


class AssetImportRequest(BaseModel):
    assets: List[AssetEntityCreate] = Field(min_length=1, max_length=1000)


class AssetEntityUpdate(BaseModel):
    source: Optional[str] = Field(default=None, max_length=128)


class AssetEntityOut(BaseModel):
    id: UUID
    project_id: UUID
    asset_type: AssetType
    value: str
    source: Optional[str] = None
    first_seen: datetime
    last_seen: datetime

    model_config = {"from_attributes": True}


class AssetImportResult(BaseModel):
    inserted: int
    skipped: int
    total: int
