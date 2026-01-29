import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from server.app.db.base import Base


class AssetEntity(Base):
    __tablename__ = "asset_entity"
    __table_args__ = (
        UniqueConstraint("project_id", "asset_type", "value", name="uq_asset_entity_key"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False, index=True)
    asset_type = Column(String(32), nullable=False, index=True)
    value = Column(String(2048), nullable=False)
    source = Column(String(128))
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
