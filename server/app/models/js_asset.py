"""JavaScript asset model."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from server.app.db.base import Base


class JSAsset(Base):
    """JavaScript asset discovered from web pages."""

    __tablename__ = "js_asset"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "script_url",
            "content_hash",
            name="uq_js_asset_key",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False, index=True)
    web_asset_id = Column(UUID(as_uuid=True), ForeignKey("web_asset.id"), nullable=True, index=True)
    script_url = Column(String(2048), nullable=False)
    script_type = Column(String(20), nullable=False, default="external")
    content_hash = Column(String(64), nullable=False, index=True)
    source_url = Column(String(2048), nullable=True)
    scan_metadata = Column(JSONB, default=dict)
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
