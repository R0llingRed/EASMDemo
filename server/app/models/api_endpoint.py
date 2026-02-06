"""API endpoint model discovered by JS analysis."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from server.app.db.base import Base


class APIEndpoint(Base):
    """Normalized API endpoint extracted from JavaScript content."""

    __tablename__ = "api_endpoint"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "endpoint",
            "method",
            name="uq_api_endpoint_key",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False, index=True)
    js_asset_id = Column(UUID(as_uuid=True), ForeignKey("js_asset.id"), nullable=True, index=True)
    endpoint = Column(String(2048), nullable=False)
    method = Column(String(10), nullable=False, default="GET", index=True)
    host = Column(String(255), nullable=True, index=True)
    source = Column(String(50), nullable=False, default="js_analysis")
    requires_auth = Column(Boolean, nullable=True)
    risk_tags = Column(JSONB, default=list)
    evidence = Column(JSONB, default=dict)
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
