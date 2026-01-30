import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from server.app.db.base import Base


class Subdomain(Base):
    __tablename__ = "subdomain"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False, index=True)
    root_domain = Column(String(255), nullable=False, index=True)
    subdomain = Column(String(512), nullable=False, index=True)
    source = Column(String(128))
    ip_addresses = Column(JSONB, default=list)
    cname = Column(Text)
    is_cdn = Column(Boolean, default=False)
    cdn_provider = Column(String(128))
    status = Column(String(32), default="active")
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
