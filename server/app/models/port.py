import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from server.app.db.base import Base


class Port(Base):
    __tablename__ = "port"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_id = Column(UUID(as_uuid=True), ForeignKey("ip_address.id"), nullable=False, index=True)
    port = Column(Integer, nullable=False)
    protocol = Column(String(16), default="tcp")
    state = Column(String(32))
    service = Column(String(128))
    version = Column(String(255))
    banner = Column(Text)
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
