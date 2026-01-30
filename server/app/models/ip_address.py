import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from server.app.db.base import Base


class IPAddress(Base):
    __tablename__ = "ip_address"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False, index=True)
    ip = Column(String(45), nullable=False, index=True)
    source = Column(String(128))
    asn = Column(String(64))
    asn_org = Column(String(255))
    country = Column(String(16))
    region = Column(String(128))
    city = Column(String(128))
    is_cdn = Column(Boolean, default=False)
    fingerprint_hash = Column(String(32), index=True)
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
