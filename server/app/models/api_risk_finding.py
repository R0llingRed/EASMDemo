"""API risk finding model."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from server.app.db.base import Base


class APIRiskFinding(Base):
    """Risk finding produced by API deep analysis rules."""

    __tablename__ = "api_risk_finding"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "endpoint_id",
            "rule_name",
            name="uq_api_risk_rule_key",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False, index=True)
    endpoint_id = Column(
        UUID(as_uuid=True),
        ForeignKey("api_endpoint.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rule_name = Column(String(128), nullable=False)
    severity = Column(String(20), nullable=False, default="medium", index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    evidence = Column(JSONB, default=dict)
    status = Column(String(20), nullable=False, default="open", index=True)
    updated_by = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    status_history = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
