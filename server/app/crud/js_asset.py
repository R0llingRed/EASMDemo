"""CRUD operations for JS assets."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from server.app.models.js_asset import JSAsset


def upsert_js_asset(
    db: Session,
    project_id: UUID,
    script_url: str,
    content_hash: str,
    script_type: str = "external",
    web_asset_id: Optional[UUID] = None,
    source_url: Optional[str] = None,
    scan_metadata: Optional[dict] = None,
) -> JSAsset:
    """Insert or update a JS asset by unique key."""
    stmt = insert(JSAsset).values(
        project_id=project_id,
        web_asset_id=web_asset_id,
        script_url=script_url,
        script_type=script_type,
        content_hash=content_hash,
        source_url=source_url,
        scan_metadata=scan_metadata or {},
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["project_id", "script_url", "content_hash"],
        set_={
            "web_asset_id": stmt.excluded.web_asset_id,
            "source_url": stmt.excluded.source_url,
            "scan_metadata": stmt.excluded.scan_metadata,
            "last_seen": func.now(),
        },
    )
    db.execute(stmt)
    db.commit()
    return db.scalars(
        select(JSAsset).where(
            JSAsset.project_id == project_id,
            JSAsset.script_url == script_url,
            JSAsset.content_hash == content_hash,
        )
    ).first()


def get_js_asset(db: Session, js_asset_id: UUID) -> Optional[JSAsset]:
    return db.get(JSAsset, js_asset_id)


def list_js_assets(
    db: Session,
    project_id: UUID,
    script_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[JSAsset]:
    stmt = select(JSAsset).where(JSAsset.project_id == project_id)
    if script_type:
        stmt = stmt.where(JSAsset.script_type == script_type)
    stmt = stmt.order_by(JSAsset.last_seen.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def count_js_assets(
    db: Session,
    project_id: UUID,
    script_type: Optional[str] = None,
) -> int:
    stmt = select(func.count()).select_from(JSAsset).where(JSAsset.project_id == project_id)
    if script_type:
        stmt = stmt.where(JSAsset.script_type == script_type)
    return db.scalar(stmt) or 0
