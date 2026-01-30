import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from server.app.db.base import Base


class WebAsset(Base):
    __tablename__ = "web_asset"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False, index=True)
    url = Column(String(2048), nullable=False, index=True)
    subdomain_id = Column(UUID(as_uuid=True), ForeignKey("subdomain.id"), nullable=True)
    ip_id = Column(UUID(as_uuid=True), ForeignKey("ip_address.id"), nullable=True)
    port_id = Column(UUID(as_uuid=True), ForeignKey("port.id"), nullable=True)
    title = Column(String(512))
    status_code = Column(Integer)
    content_length = Column(Integer)
    content_type = Column(String(255))
    server = Column(String(255))
    technologies = Column(JSONB, default=list)
    fingerprints = Column(JSONB, default=list)
    headers = Column(JSONB, default=dict)
    screenshot_path = Column(String(512))
    response_hash = Column(String(64))
    is_alive = Column(Boolean, default=True)
    fingerprint_hash = Column(String(32), index=True)
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
